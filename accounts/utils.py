"""
Utility functions for email verification and password reset
"""
import random
import string
import time
import logging
from django.utils import timezone
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.db import models
from .models import EmailVerification

logger = logging.getLogger(__name__)


def generate_verification_code(length=6):
    """Generate a random numeric verification code"""
    return ''.join(random.choices(string.digits, k=length))


def send_verification_email(email, code, verification_type='REGISTRATION', user=None):
    """Send verification code email with retry logic and improved error handling"""
    import smtplib
    import socket
    
    # Validate email configuration before attempting to send
    if not settings.EMAIL_HOST_PASSWORD:
        error_msg = "Email service is not configured. Please contact support."
        logger.error(f"Email configuration error: EMAIL_HOST_PASSWORD is not set")
        raise ValueError(error_msg)
    
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
    
    # Render email templates
    try:
        html_message = render_to_string(template_name, context)
        text_message = render_to_string(text_template, context)
    except Exception as e:
        verification.delete()
        logger.error(f"Failed to render email templates: {e}")
        raise ValueError(f"Failed to prepare email: {str(e)}")
    
    # Retry logic: attempt to send email up to 3 times
    max_retries = 3
    retry_delay = 2  # seconds
    
    for attempt in range(1, max_retries + 1):
        try:
            # Use EmailMultiAlternatives for better control
            email_msg = EmailMultiAlternatives(
                subject=subject,
                body=text_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[email]
            )
            email_msg.attach_alternative(html_message, "text/html")
            email_msg.send(fail_silently=False)
            
            logger.info(f"Verification email sent successfully to {email} (attempt {attempt})")
            return verification
            
        except (smtplib.SMTPException, socket.error, ConnectionError, OSError) as e:
            error_type = type(e).__name__
            error_msg = str(e)
            
            # Log the error with context
            logger.warning(
                f"Email send attempt {attempt}/{max_retries} failed for {email}: "
                f"{error_type}: {error_msg}"
            )
            
            # If this is the last attempt, provide a user-friendly error message
            if attempt == max_retries:
                verification.delete()
                
                # Provide specific error messages based on error type
                if "connection" in error_msg.lower() or "closed" in error_msg.lower():
                    user_error = (
                        "Unable to connect to email service. This may be due to: "
                        "1) Email service configuration issue, 2) Network connectivity problem, "
                        "or 3) Email service temporarily unavailable. Please try again in a few moments."
                    )
                elif "authentication" in error_msg.lower() or "535" in error_msg:
                    user_error = (
                        "Email authentication failed. Please contact support to verify "
                        "email service configuration."
                    )
                elif "timeout" in error_msg.lower():
                    user_error = (
                        "Email service connection timed out. Please try again in a few moments."
                    )
                else:
                    user_error = (
                        f"Failed to send email: {error_msg}. "
                        "Please try again or contact support if the problem persists."
                    )
                
                raise ConnectionError(user_error)
            
            # Wait before retrying (exponential backoff)
            time.sleep(retry_delay * attempt)
            
        except Exception as e:
            # For unexpected errors, don't retry
            verification.delete()
            error_msg = str(e)
            logger.error(f"Unexpected error sending verification email to {email}: {error_msg}")
            raise ValueError(f"Failed to send email due to an unexpected error: {error_msg}")


def send_welcome_email(user, password):
    """Send welcome email with account credentials"""
    import smtplib
    import socket
    
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
        
        # Use EmailMultiAlternatives for better control
        email_msg = EmailMultiAlternatives(
            subject=subject,
            body=text_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email]
        )
        email_msg.attach_alternative(html_message, "text/html")
        email_msg.send(fail_silently=False)
        
        logger.info(f"Welcome email sent successfully to {user.email}")
    except (smtplib.SMTPException, socket.error, ConnectionError, OSError) as e:
        # Log error but don't fail registration
        logger.error(f"Failed to send welcome email to {user.email}: {str(e)}")
    except Exception as e:
        # Log unexpected errors
        logger.error(f"Unexpected error sending welcome email to {user.email}: {str(e)}")


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

