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
from .models import User, UserProfile, UserRating, UserGallery, EmailVerification
from .forms import UserRegistrationForm, UserLoginForm, ProfileUpdateForm, ProfileSetupForm, GalleryImageForm, GalleryImageUpdateForm
from .utils import generate_verification_code, send_verification_email, send_welcome_email, verify_code
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
    """User registration with email verification"""
    # Capture referral code from query string and store in session so it survives validation errors
    ref_code = request.GET.get('ref')
    if ref_code:
        request.session['referral_code'] = ref_code
        request.session.modified = True

    if request.method == 'POST':
        form = UserRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            # Create user but don't activate yet
            user = form.save(commit=False)
            user.is_active = False  # User must verify email first
            password = form.cleaned_data['password1']  # Save password before hashing
            user.set_password(password)

            # Attach referrer if present and this is a female user
            try:
                stored_ref = request.session.get('referral_code') or request.GET.get('ref')
                if stored_ref and user.user_type == 'F':
                    referrer = User.objects.filter(referral_code=stored_ref).first()
                    if referrer and referrer != user:
                        user.referred_by = referrer
            except Exception:
                # Never break registration because of referral issues
                pass

            user.save()
            
            # Create user profile and mark email as unverified
            profile, created = UserProfile.objects.get_or_create(user=user)
            profile.email_verified = False
            profile.save()
            
            # Generate and send verification code
            code = generate_verification_code()
            try:
                send_verification_email(user.email, code, 'REGISTRATION', user)
                messages.success(request, f'✅ Registration successful! A verification code has been sent to {user.email}. Please check your email and enter the code to activate your account.')
                # Store user ID and password in session for verification step
                request.session['pending_verification_user_id'] = user.id
                request.session['pending_verification_email'] = user.email
                request.session['pending_verification_password'] = password  # Store plain password for welcome email
                request.session.modified = True  # Ensure session is saved
                return redirect('accounts:verify_email')
            except (ConnectionError, ValueError) as e:
                # These are user-friendly errors from send_verification_email
                user.delete()
                error_msg = str(e)
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Registration email error for {user.email}: {error_msg}")
                messages.error(request, f'❌ Registration failed: {error_msg}. Please try again in a few moments.')
            except Exception as e:
                # If email sending fails, delete user and show error
                user.delete()
                error_msg = str(e)
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Unexpected registration email error for {user.email}: {error_msg}")
                messages.error(request, f'❌ Registration failed: Could not send verification email. Please try again in a few moments. If the problem persists, contact support.')
        else:
            # Form validation failed - show errors
            messages.error(request, '❌ Please correct the errors below and try again.')
            # Individual field errors will be shown in the form
    else:
        form = UserRegistrationForm()
    
    return render(request, 'accounts/register.html', {'form': form})


def verify_email(request):
    """Email verification page"""
    # Get session data - but don't redirect on GET requests if missing (allow user to see the page)
    user_id = request.session.get('pending_verification_user_id')
    email = request.session.get('pending_verification_email')
    
    # Only check session on POST requests or if we need to show an error
    if request.method == 'POST':
        if not user_id or not email:
            messages.error(request, '❌ No pending verification found. Your session may have expired. Please register again.')
            return redirect('accounts:register')
        
        try:
            user = User.objects.get(id=user_id, email=email)
        except User.DoesNotExist:
            messages.error(request, '❌ Invalid verification session. The user account was not found. Please register again.')
            # Clear invalid session
            request.session.pop('pending_verification_user_id', None)
            request.session.pop('pending_verification_email', None)
            request.session.pop('pending_verification_password', None)
            return redirect('accounts:register')
        
        code = request.POST.get('code', '').strip()
        
        if not code:
            messages.error(request, '❌ Please enter the 6-digit verification code sent to your email.')
            return render(request, 'accounts/verify_email.html', {'email': email, 'user_id': user_id})
        
        if len(code) != 6 or not code.isdigit():
            messages.error(request, '❌ Invalid code format. Please enter the 6-digit code sent to your email.')
            return render(request, 'accounts/verify_email.html', {'email': email, 'user_id': user_id})
        
        # Verify the code
        try:
            verification, error = verify_code(email, code, 'REGISTRATION')
            
            if verification and not error:
                # Activate user account
                user.is_active = True
                user.save()
                
                # Update profile
                profile, created = UserProfile.objects.get_or_create(user=user)
                profile.email_verified = True
                profile.save()
                
                # Get the original password from session
                password = request.session.get('pending_verification_password')
                
                # Login user - ensure backend is specified
                login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                
                # Verify login was successful
                if not request.user.is_authenticated:
                    messages.error(request, '❌ Failed to log you in automatically. Please try logging in manually with your credentials.')
                    return redirect('accounts:login')
                
                # Send welcome email with credentials
                try:
                    send_welcome_email(user, password if password else 'Your chosen password')
                except Exception as e:
                    print(f"Failed to send welcome email: {e}")
                    # Don't fail the verification if email fails
                
                # Clear session
                request.session.pop('pending_verification_user_id', None)
                request.session.pop('pending_verification_email', None)
                request.session.pop('pending_verification_password', None)
                
                messages.success(request, '✅ Email verified successfully! Your account has been activated. Welcome to MjoloBid!')
                # Ensure message persists through redirect
                request.session['verification_success'] = True
                return redirect('accounts:profile_setup')
            else:
                # Provide specific error message and STAY ON THE SAME PAGE
                error_msg = error or 'Invalid verification code. Please check the code and try again.'
                messages.error(request, f'❌ {error_msg}')
                # IMPORTANT: Stay on verification page to show error - don't redirect!
                # Save session to ensure it persists
                request.session['pending_verification_user_id'] = user_id
                request.session['pending_verification_email'] = email
                request.session.modified = True
                return render(request, 'accounts/verify_email.html', {'email': email, 'user_id': user_id})
        except Exception as e:
            error_msg = str(e)
            print(f"Verification error: {e}")
            import traceback
            traceback.print_exc()
            messages.error(request, f'❌ An error occurred during verification: {error_msg}. Please try again or request a new code.')
            # IMPORTANT: Stay on verification page to show error - don't redirect!
            # Save session to ensure it persists
            request.session['pending_verification_user_id'] = user_id
            request.session['pending_verification_email'] = email
            request.session.modified = True
            return render(request, 'accounts/verify_email.html', {'email': email, 'user_id': user_id})
    
    # GET request - show verification page
    if not user_id or not email:
        messages.error(request, '❌ No pending verification found. Your session may have expired. Please register again.')
        return redirect('accounts:register')
    
    try:
        user = User.objects.get(id=user_id, email=email)
    except User.DoesNotExist:
        messages.error(request, '❌ Invalid verification session. The user account was not found. Please register again.')
        # Clear invalid session
        request.session.pop('pending_verification_user_id', None)
        request.session.pop('pending_verification_email', None)
        request.session.pop('pending_verification_password', None)
        return redirect('accounts:register')
    
    return render(request, 'accounts/verify_email.html', {'email': email, 'user_id': user_id})


def resend_verification_code(request):
    """Resend verification code"""
    user_id = request.session.get('pending_verification_user_id')
    email = request.session.get('pending_verification_email')
    
    if not user_id or not email:
        return JsonResponse({'success': False, 'error': 'No pending verification found. Please register again.'})
    
    try:
        user = User.objects.get(id=user_id, email=email)
        code = generate_verification_code()
        send_verification_email(email, code, 'REGISTRATION', user)
        return JsonResponse({'success': True, 'message': '✅ A new verification code has been sent to your email. Please check your inbox.'})
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'User account not found. Please register again.'})
    except (ConnectionError, ValueError) as e:
        # These are user-friendly errors from send_verification_email
        error_msg = str(e)
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error resending verification code to {email}: {error_msg}")
        return JsonResponse({'success': False, 'error': error_msg})
    except Exception as e:
        error_msg = str(e)
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Unexpected error resending verification code to {email}: {error_msg}")
        return JsonResponse({'success': False, 'error': 'Failed to send verification code. Please try again in a few moments. If the problem persists, contact support.'})


def forgot_password(request):
    """Forgot password - request verification code"""
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        
        if not email:
            messages.error(request, '❌ Please enter your email address.')
            return render(request, 'accounts/forgot_password.html')
        
        # Basic email format validation
        if '@' not in email or '.' not in email.split('@')[-1]:
            messages.error(request, '❌ Please enter a valid email address.')
            return render(request, 'accounts/forgot_password.html')
        
        try:
            user = User.objects.get(email=email)
            # Generate and send verification code
            code = generate_verification_code()
            send_verification_email(email, code, 'PASSWORD_RESET', user)
            messages.success(request, f'✅ A password reset code has been sent to {email}. Please check your email.')
            request.session['password_reset_email'] = email
            return redirect('accounts:verify_password_reset')
        except User.DoesNotExist:
            # Don't reveal if email exists or not (security best practice)
            messages.success(request, '✅ If an account exists with that email, a password reset code has been sent. Please check your inbox.')
            return redirect('accounts:login')
        except (ConnectionError, ValueError) as e:
            # These are user-friendly errors from send_verification_email
            error_msg = str(e)
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error sending password reset code to {email}: {error_msg}")
            messages.error(request, f'❌ {error_msg}')
        except Exception as e:
            error_msg = str(e)
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Unexpected error sending password reset code to {email}: {error_msg}")
            messages.error(request, f'❌ Failed to send password reset code. Please try again in a few moments. If the problem persists, contact support.')
    
    return render(request, 'accounts/forgot_password.html')


def verify_password_reset(request):
    """Verify password reset code"""
    email = request.session.get('password_reset_email')
    
    if not email:
        messages.error(request, '❌ No password reset request found. Your session may have expired. Please start over.')
        return redirect('accounts:forgot_password')
    
    if request.method == 'POST':
        code = request.POST.get('code', '').strip()
        
        if not code:
            messages.error(request, '❌ Please enter the 6-digit verification code sent to your email.')
            return render(request, 'accounts/verify_password_reset.html', {'email': email})
        
        if len(code) != 6 or not code.isdigit():
            messages.error(request, '❌ Invalid code format. Please enter the 6-digit code sent to your email.')
            return render(request, 'accounts/verify_password_reset.html', {'email': email})
        
        # Verify the code
        try:
            verification, error = verify_code(email, code, 'PASSWORD_RESET')
            
            if verification and not error:
                # Store verification status in session for password reset step
                request.session['password_reset_verified'] = True
                request.session['password_reset_email'] = email
                messages.success(request, '✅ Code verified successfully! Please enter your new password.')
                return redirect('accounts:reset_password')
            else:
                error_msg = error or 'Invalid verification code. Please check the code and try again.'
                messages.error(request, f'❌ {error_msg}')
        except Exception as e:
            messages.error(request, f'❌ An error occurred during verification: {str(e)}. Please try again.')
            print(f"Password reset verification error: {e}")
    
    return render(request, 'accounts/verify_password_reset.html', {'email': email})


def reset_password(request):
    """Reset password after verification"""
    email = request.session.get('password_reset_email')
    verified = request.session.get('password_reset_verified')
    
    if not email or not verified:
        messages.error(request, '❌ Please verify your email first. Your session may have expired.')
        return redirect('accounts:forgot_password')
    
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        messages.error(request, '❌ User account not found. Please register again.')
        # Clear session
        request.session.pop('password_reset_email', None)
        request.session.pop('password_reset_verified', None)
        return redirect('accounts:forgot_password')
    
    if request.method == 'POST':
        password1 = request.POST.get('password1', '').strip()
        password2 = request.POST.get('password2', '').strip()
        
        if not password1 or not password2:
            messages.error(request, '❌ Please fill in both password fields.')
            return render(request, 'accounts/reset_password.html')
        
        if password1 != password2:
            messages.error(request, '❌ Passwords do not match. Please enter the same password in both fields.')
            return render(request, 'accounts/reset_password.html')
        
        if len(password1) < 8:
            messages.error(request, '❌ Password must be at least 8 characters long. Please choose a stronger password.')
            return render(request, 'accounts/reset_password.html')
        
        try:
            # Set new password
            user.set_password(password1)
            user.save()
            
            # Clear session
            request.session.pop('password_reset_email', None)
            request.session.pop('password_reset_verified', None)
            
            messages.success(request, '✅ Password reset successfully! You can now login with your new password.')
            return redirect('accounts:login')
        except Exception as e:
            messages.error(request, f'❌ Failed to reset password: {str(e)}. Please try again.')
            print(f"Password reset error: {e}")
    
    return render(request, 'accounts/reset_password.html')


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
        # Clear any pre-existing (non-error) messages on initial load
        for _ in messages.get_messages(request):
            pass
        form = UserLoginForm()
    
    return render(request, 'accounts/login.html', {'form': form})


@login_required
def user_logout(request):
    """User logout"""
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('accounts:home')


@login_required
def profile_setup(request):
    """Profile setup after registration"""
    # Check if user just verified their email (first time on this page after verification)
    # The success message should already be in messages from the redirect, but ensure it's there
    verification_success_shown = request.session.get('verification_success_shown', False)
    if not verification_success_shown:
        # Check if there's already a success message about verification
        existing_messages = list(messages.get_messages(request))
        has_verification_message = any('verified successfully' in str(m).lower() or 'account has been activated' in str(m).lower() for m in existing_messages)
        
        if not has_verification_message:
            # Add the verification success message
            messages.success(request, '✅ Email verified successfully! Your account has been activated. Welcome to MjoloBid!')
        
        # Mark as shown so we don't show it again on refresh
        request.session['verification_success_shown'] = True
        request.session.modified = True
    
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
    
    return render(request, 'accounts/profile_setup.html', {'form': form, 'hide_navbar': True})


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


@login_required
def gallery(request):
    """User gallery management"""
    gallery_images = UserGallery.objects.filter(user=request.user).order_by('-is_primary', '-uploaded_at')
    
    context = {
        'gallery_images': gallery_images,
    }
    
    return render(request, 'accounts/gallery.html', context)


@login_required
def upload_gallery_image(request):
    """Upload a new gallery image"""
    if request.method == 'POST':
        form = GalleryImageForm(request.POST, request.FILES)
        if form.is_valid():
            gallery_image = form.save(commit=False)
            gallery_image.user = request.user
            gallery_image.save()
            messages.success(request, 'Image uploaded successfully!')
            return redirect('accounts:gallery')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = GalleryImageForm()
    
    return render(request, 'accounts/upload_gallery_image.html', {'form': form})


@login_required
def edit_gallery_image(request, image_id):
    """Edit gallery image details"""
    try:
        gallery_image = UserGallery.objects.get(id=image_id, user=request.user)
    except UserGallery.DoesNotExist:
        messages.error(request, 'Image not found.')
        return redirect('accounts:gallery')
    
    if request.method == 'POST':
        form = GalleryImageUpdateForm(request.POST, instance=gallery_image)
        if form.is_valid():
            form.save()
            messages.success(request, 'Image updated successfully!')
            return redirect('accounts:gallery')
    else:
        form = GalleryImageUpdateForm(instance=gallery_image)
    
    return render(request, 'accounts/edit_gallery_image.html', {'form': form, 'gallery_image': gallery_image})


@login_required
def delete_gallery_image(request, image_id):
    """Delete a gallery image"""
    try:
        gallery_image = UserGallery.objects.get(id=image_id, user=request.user)
        gallery_image.delete()
        messages.success(request, 'Image deleted successfully!')
    except UserGallery.DoesNotExist:
        messages.error(request, 'Image not found.')
    
    return redirect('accounts:gallery')


@login_required
def set_primary_image(request, image_id):
    """Set an image as primary"""
    try:
        gallery_image = UserGallery.objects.get(id=image_id, user=request.user)
        gallery_image.is_primary = True
        gallery_image.save()
        messages.success(request, 'Primary image updated!')
    except UserGallery.DoesNotExist:
        messages.error(request, 'Image not found.')
    
    return redirect('accounts:gallery')


@login_required
def view_user_profile(request, user_id):
    """View another user's profile"""
    try:
        viewed_user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        messages.error(request, 'User not found.')
        return redirect('accounts:home')
    
    # Get user profile
    try:
        user_profile = viewed_user.profile
    except UserProfile.DoesNotExist:
        user_profile = UserProfile.objects.create(user=viewed_user)
    
    # Get user's ratings
    ratings = UserRating.objects.filter(rated_user=viewed_user).order_by('-created_at')[:5]
    
    # Get gallery images (limited to 6 for preview)
    gallery_images = UserGallery.objects.filter(user=viewed_user).order_by('-is_primary', '-uploaded_at')[:6]
    
    # Check if viewing own profile
    is_own_profile = (request.user == viewed_user)
    
    context = {
        'viewed_user': viewed_user,
        'user_profile': user_profile,
        'ratings': ratings,
        'gallery_images': gallery_images,
        'is_own_profile': is_own_profile,
    }
    
    return render(request, 'accounts/view_user_profile.html', context)


@login_required
def view_user_gallery(request, user_id):
    """View another user's gallery"""
    try:
        viewed_user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        messages.error(request, 'User not found.')
        return redirect('accounts:home')
    
    gallery_images = UserGallery.objects.filter(user=viewed_user).order_by('-is_primary', '-uploaded_at')
    
    # Check if viewing own gallery
    is_own_gallery = (request.user == viewed_user)
    
    context = {
        'viewed_user': viewed_user,
        'gallery_images': gallery_images,
        'is_own_gallery': is_own_gallery,
    }
    
    return render(request, 'accounts/view_user_gallery.html', context)
