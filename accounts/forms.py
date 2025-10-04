from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, UserProfile


class UserRegistrationForm(UserCreationForm):
    """Custom user registration form"""
    
    email = forms.EmailField(required=True)
    phone_number = forms.CharField(max_length=15, required=True)
    gender = forms.ChoiceField(choices=User.GENDER_CHOICES, required=False)
    user_type = forms.ChoiceField(choices=User.USER_TYPE_CHOICES, required=True)
    date_of_birth = forms.DateField(required=True, widget=forms.DateInput(attrs={'type': 'date'}))
    city = forms.CharField(max_length=100, required=True)
    bio = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), required=False)
    profile_picture = forms.ImageField(required=False)
    
    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2', 'phone_number', 
                 'gender', 'user_type', 'date_of_birth', 'city', 'bio', 'profile_picture')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].help_text = None
        self.fields['password1'].help_text = None
        self.fields['password2'].help_text = None
        # If the template doesn't render a gender input, derive it from user_type
        # to prevent validation failures.
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('This email is already registered.')
        return email
    
    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')
        if User.objects.filter(phone_number=phone_number).exists():
            raise forms.ValidationError('This phone number is already registered.')
        return phone_number

    def clean(self):
        cleaned_data = super().clean()
        user_type = cleaned_data.get('user_type')
        gender = cleaned_data.get('gender')
        # If gender is not provided by the form, infer it from user_type
        if not gender and user_type in dict(User.USER_TYPE_CHOICES):
            cleaned_data['gender'] = 'M' if user_type == 'M' else 'F'
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        # Ensure gender is set on the instance
        user.gender = self.cleaned_data.get('gender') or (
            'M' if self.cleaned_data.get('user_type') == 'M' else 'F'
        )
        if commit:
            user.save()
        return user


class UserLoginForm(forms.Form):
    """User login form"""
    
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)


class ProfileUpdateForm(forms.ModelForm):
    """Profile update form"""
    
    class Meta:
        model = User
        fields = ('email', 'phone_number', 'bio', 'profile_picture', 'city', 'location')
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 3}),
        }


class ProfileSetupForm(forms.ModelForm):
    """Profile setup form with only the fields shown on the setup page"""
    class Meta:
        model = User
        fields = ('bio', 'profile_picture', 'city', 'location')
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ensure we don't overwrite required fields that aren't in this form
        if self.instance and self.instance.pk:
            # Preserve existing gender and user_type
            self.fields['bio'].initial = self.instance.bio
            self.fields['city'].initial = self.instance.city
            self.fields['location'].initial = self.instance.location
            
            # If user already has a profile picture, make it optional
            if self.instance.profile_picture:
                self.fields['profile_picture'].required = False
                self.fields['profile_picture'].help_text = "Leave empty to keep current profile picture"
    
    def clean_profile_picture(self):
        picture = self.cleaned_data.get('profile_picture')
        print(f"DEBUG: Cleaning profile picture: {picture}")
        if picture:
            print(f"DEBUG: Picture type: {type(picture)}")
            print(f"DEBUG: Picture name: {getattr(picture, 'name', 'No name')}")
            print(f"DEBUG: Picture size: {getattr(picture, 'size', 'No size')}")
            if hasattr(picture, 'content_type'):
                print(f"DEBUG: Picture has content_type: {picture.content_type}")
                # Check file size (max 5MB)
                if picture.size > 5 * 1024 * 1024:
                    raise forms.ValidationError('Image file too large (max 5MB)')
                
                # Check file type
                if not picture.content_type.startswith('image/'):
                    raise forms.ValidationError('File must be an image')
            else:
                print(f"DEBUG: Picture exists but no content_type: {type(picture)}")
        
        return picture
    
    def save(self, commit=True):
        # Only update the fields that are in this form
        user = self.instance
        print(f"DEBUG: Saving user {user.username}")
        print(f"DEBUG: Cleaned data: {self.cleaned_data}")
        
        user.bio = self.cleaned_data.get('bio', '')
        if self.cleaned_data.get('profile_picture'):
            print(f"DEBUG: Setting profile picture: {self.cleaned_data['profile_picture']}")
            user.profile_picture = self.cleaned_data['profile_picture']
        user.city = self.cleaned_data.get('city', user.city)
        user.location = self.cleaned_data.get('location', '')
        
        if commit:
            user.save()
            print(f"DEBUG: User saved. Profile picture: {user.profile_picture}")
        return user

class UserProfileForm(forms.ModelForm):
    """Extended user profile form"""
    
    class Meta:
        model = UserProfile
        fields = ('occupation', 'education', 'interests', 'instagram', 'twitter', 
                 'preferred_events', 'max_distance')
        widgets = {
            'interests': forms.Textarea(attrs={'rows': 3}),
            'preferred_events': forms.CheckboxSelectMultiple,
        }
