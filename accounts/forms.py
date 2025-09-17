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
