from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db.models import Q
from django.conf import settings
import os
from .models import User, UserProfile, UserRating
from .forms import UserRegistrationForm, UserLoginForm, ProfileUpdateForm, ProfileSetupForm
import json


def home(request):
    """Home page with intro popup"""
    if request.user.is_authenticated:
        if request.user.is_staff or request.user.is_superuser:
            return redirect('/dashboard/')
        elif request.user.user_type == 'M':
            return redirect('bids:male_homepage')
        else:
            return redirect('bids:browse_bids')
    
    return render(request, 'accounts/home.html')


def register(request):
    """User registration"""
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Account created successfully!')
            return redirect('accounts:profile_setup')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'accounts/register.html', {'form': form})


def user_login(request):
    """User login"""
    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                login(request, user)
                user.last_seen = timezone.now()
                user.save()
                messages.success(request, 'Welcome back!')
                
                # Redirect based on user type
                if user.user_type == 'M':
                    return redirect('bids:my_bids')
                else:
                    return redirect('bids:browse_bids')
            else:
                messages.error(request, 'Invalid username or password.')
    else:
        form = UserLoginForm()
    
    return render(request, 'accounts/login.html', {'form': form})


def user_logout(request):
    """User logout"""
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('accounts:home')


@login_required
def profile_setup(request):
    """Profile setup after registration"""
    if request.method == 'POST':
        form = ProfileSetupForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Profile updated successfully!')
            profile_url = f"{reverse('accounts:profile')}?setup=done"
            return redirect(profile_url)
        else:
            # Show form errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = ProfileSetupForm(instance=request.user)
    
    return render(request, 'accounts/profile_setup.html', {'form': form})


@login_required
def profile(request):
    """User profile view"""
    try:
        user_profile = request.user.profile
    except UserProfile.DoesNotExist:
        user_profile = UserProfile.objects.create(user=request.user)
    
    # Get user's ratings
    ratings = UserRating.objects.filter(rated_user=request.user).order_by('-created_at')[:5]
    
    profile_setup_success = request.GET.get('setup') == 'done'

    context = {
        'user_profile': user_profile,
        'ratings': ratings,
        'profile_setup_success': profile_setup_success,
    }
    
    return render(request, 'accounts/profile.html', context)


def test_media(request):
    """Test view to check media file serving"""
    media_files = []
    media_dir = settings.MEDIA_ROOT / 'profile_pics'
    if media_dir.exists():
        for file in media_dir.iterdir():
            if file.is_file():
                media_files.append({
                    'name': file.name,
                    'path': str(file),
                    'url': f"{settings.MEDIA_URL}profile_pics/{file.name}"
                })
    
    # Also check current user's profile picture
    user_profile_pic = None
    if request.user.is_authenticated:
        if request.user.profile_picture:
            user_profile_pic = {
                'name': request.user.profile_picture.name,
                'url': request.user.profile_picture.url,
                'path': str(request.user.profile_picture.path) if request.user.profile_picture.path else None
            }
    
    return JsonResponse({
        'media_root': str(settings.MEDIA_ROOT),
        'media_url': settings.MEDIA_URL,
        'files': media_files,
        'user_profile_pic': user_profile_pic,
        'debug': settings.DEBUG,
        'authenticated': request.user.is_authenticated
    })


def test_upload(request):
    """Test view to manually test file upload"""
    if request.method == 'POST' and request.FILES:
        # Get the first file
        file = list(request.FILES.values())[0]
        
        # Save it to the user's profile
        if request.user.is_authenticated:
            request.user.profile_picture = file
            request.user.save()
            
            return JsonResponse({
                'success': True,
                'message': 'File uploaded successfully',
                'filename': file.name,
                'profile_picture_url': request.user.profile_picture.url if request.user.profile_picture else None,
                'profile_picture_path': str(request.user.profile_picture.path) if request.user.profile_picture else None
            })
    
    return JsonResponse({
        'success': False,
        'message': 'No file uploaded or user not authenticated'
    })




@login_required
def edit_profile(request):
    """Edit user profile"""
    try:
        user_profile = request.user.profile
    except UserProfile.DoesNotExist:
        user_profile = UserProfile.objects.create(user=request.user)
    
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('accounts:profile')
    else:
        form = ProfileUpdateForm(instance=request.user)
    
    return render(request, 'accounts/edit_profile.html', {'form': form})


@login_required
def premium_upgrade(request):
    """Premium upgrade page"""
    return render(request, 'accounts/premium_upgrade.html')


@login_required
def affiliate_dashboard(request):
    """Affiliate dashboard"""
    referrals = User.objects.filter(referred_by=request.user)
    
    context = {
        'referrals': referrals,
        'total_referrals': request.user.total_referrals,
        'referral_earnings': request.user.referral_earnings,
        'referral_code': request.user.referral_code,
    }
    
    return render(request, 'accounts/affiliate_dashboard.html', context)


@login_required
@csrf_exempt
def update_location(request):
    """Update user location via AJAX"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            latitude = data.get('latitude')
            longitude = data.get('longitude')
            
            if latitude and longitude:
                request.user.latitude = latitude
                request.user.longitude = longitude
                request.user.save()
                
                return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request'})


@login_required
def rate_user(request, user_id):
    """Rate another user"""
    if request.method == 'POST':
        rated_user = User.objects.get(id=user_id)
        rating = request.POST.get('rating')
        review = request.POST.get('review', '')
        
        if rating:
            UserRating.objects.update_or_create(
                rated_user=rated_user,
                rating_user=request.user,
                defaults={
                    'rating': rating,
                    'review': review
                }
            )
            
            # Update average rating
            ratings = UserRating.objects.filter(rated_user=rated_user)
            if ratings.exists():
                avg_rating = sum(r.rating for r in ratings) / ratings.count()
                rated_user.profile.average_rating = round(avg_rating, 2)
                rated_user.profile.total_reviews = ratings.count()
                rated_user.profile.save()
            
            messages.success(request, 'Rating submitted successfully!')
    
    return redirect('accounts:profile')
