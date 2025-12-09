"""
Utility functions for email verification and password reset
"""
import random
import string
from django.utils import timezone
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.db import models
from .models import EmailVerification


def generate_verification_code(length=6):
    """Generate a random numeric verification code"""
    return ''.join(random.choices(string.digits, k=length))


def send_verification_email(email, code, verification_type='REGISTRATION', user=None):
    """Send verification code email"""
    from django.template.loader import render_to_string
    from django.core.mail import EmailMultiAlternatives
    
    # Create expiration time (15 minutes from now)
    expires_at = timezone.now() + timezone.timedelta(minutes=15)
    
    # Invalidate any existing unused codes for this email and type
    EmailVerification.objects.filter(
        email=email,
        verification_type=verification_type,
        is_used=False
    ).update(is_used=True)
    
    # Create new verification record
    verification = EmailVerification.objects.create(
        email=email,
        code=code,
        verification_type=verification_type,
        user=user,
        expires_at=expires_at
    )
    
    # Prepare email context
    if verification_type == 'REGISTRATION':
        subject = 'Verify Your MjoloBid Account'
        template_name = 'accounts/emails/verification_code.html'
        text_template = 'accounts/emails/verification_code.txt'
    else:  # PASSWORD_RESET
        subject = 'Password Reset Verification Code'
        template_name = 'accounts/emails/password_reset_code.html'
        text_template = 'accounts/emails/password_reset_code.txt'
    
    context = {
        'code': code,
        'email': email,
        'expires_in_minutes': 15,
        'verification_type': verification_type,
    }
    
    try:
        # Render HTML email
        html_message = render_to_string(template_name, context)
        text_message = render_to_string(text_template, context)
        
        # Send email
        send_mail(
            subject=subject,
            message=text_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            html_message=html_message,
            fail_silently=False,
        )
        
        return verification
    except Exception as e:
        # If email sending fails, delete the verification record
        verification.delete()
        raise e


def send_welcome_email(user, password):
    """Send welcome email with account credentials"""
    from django.template.loader import render_to_string
    from django.core.mail import EmailMultiAlternatives
    
    subject = 'Welcome to MjoloBid - Your Account Details'
    
    context = {
        'user': user,
        'username': user.username,
        'email': user.email,
        'password': password,  # Plain password for first-time users
        'login_url': f"{settings.SITE_URL}/accounts/login/",
    }
    
    try:
        html_message = render_to_string('accounts/emails/welcome.html', context)
        text_message = render_to_string('accounts/emails/welcome.txt', context)
        
        send_mail(
            subject=subject,
            message=text_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
    except Exception as e:
        # Log error but don't fail registration
        print(f"Failed to send welcome email: {e}")


def verify_code(email, code, verification_type='REGISTRATION'):
    """Verify a code for an email"""
    try:
        # First check if code format is valid
        if not code or len(code) != 6 or not code.isdigit():
            return None, "Invalid code format. Please enter the 6-digit code sent to your email."
        
        # Try to get the verification code
        try:
            verification = EmailVerification.objects.get(
                email=email,
                code=code,
                verification_type=verification_type,
                is_used=False
            )
        except EmailVerification.DoesNotExist:
            # Code doesn't exist or is already used
            # Check if there are any valid (unused, not expired) codes for this email
            from django.db.models import F
            from django.utils import timezone
            
            valid_codes = EmailVerification.objects.filter(
                email=email,
                verification_type=verification_type,
                is_used=False,
                expires_at__gt=timezone.now()
            )
            
            if valid_codes.exists():
                # There's a valid code but it doesn't match - increment attempts
                valid_codes.update(attempts=F('attempts') + 1)
                return None, "The code you entered doesn't match. Please check the code carefully and try again. Make sure you're entering all 6 digits."
            else:
                # Check if there are expired codes
                expired_codes = EmailVerification.objects.filter(
                    email=email,
                    verification_type=verification_type,
                    is_used=False
                )
                
                if expired_codes.exists():
                    return None, "Your verification code has expired (codes expire after 15 minutes). Please click 'Resend Code' to get a new one."
                else:
                    return None, "No verification code found for this email. Please request a new code."
        
        # Check if expired
        if verification.is_expired():
            verification.attempts += 1
            verification.save(update_fields=['attempts'])
            return None, "Verification code has expired (codes expire after 15 minutes). Please click 'Resend Code' to get a new one."
        
        # Mark as used
        verification.mark_as_used()
        return verification, None
        
    except Exception as e:
        # Catch any other unexpected errors
        import traceback
        print(f"Error verifying code: {e}")
        traceback.print_exc()
        return None, f"An error occurred while verifying your code: {str(e)}. Please try again or request a new code."

