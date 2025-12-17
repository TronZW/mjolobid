#!/usr/bin/env python
"""
Test SendGrid email configuration
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mjolobid.settings')
django.setup()

from django.core.mail import send_mail, EmailMultiAlternatives
from django.conf import settings

print("=" * 60)
print("SendGrid Email Configuration Test")
print("=" * 60)

# Display current settings
print("\n📧 Current Email Settings:")
print(f"  EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
print(f"  EMAIL_HOST: {settings.EMAIL_HOST}")
print(f"  EMAIL_PORT: {settings.EMAIL_PORT}")
print(f"  EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
print(f"  EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
if settings.EMAIL_HOST_PASSWORD:
    print(f"  EMAIL_HOST_PASSWORD: {settings.EMAIL_HOST_PASSWORD[:20]}...")
else:
    print("  EMAIL_HOST_PASSWORD: (not set)")
print(f"  DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")

# Test email sending
print("\n🧪 Testing Email Send...")
print("  Sending test email...")

try:
    # Get test email from user or use a default
    test_email = input("\n  Enter your email address to test: ").strip()
    
    if not test_email:
        print("  ❌ No email address provided. Exiting.")
        exit(1)
    
    # Send test email
    subject = "Test Email from MjoloBid - SendGrid"
    message = """
    This is a test email from MjoloBid using SendGrid.
    
    If you received this email, your SendGrid configuration is working correctly!
    
    Configuration Details:
    - Email Host: {host}
    - From Email: {from_email}
    - Using SendGrid SMTP
    
    Best regards,
    MjoloBid Team
    """.format(
        host=settings.EMAIL_HOST,
        from_email=settings.DEFAULT_FROM_EMAIL
    )
    
    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[test_email],
        fail_silently=False,
    )
    
    print(f"\n  ✅ Email sent successfully to {test_email}!")
    print("  📬 Please check your inbox (and spam folder) for the test email.")
    print("\n  If you don't receive it, check:")
    print("    1. SendGrid dashboard for delivery status")
    print("    2. Domain verification status in SendGrid")
    print("    3. API key permissions in SendGrid")
    print("    4. Spam/junk folder")
    
except Exception as e:
    print(f"\n  ❌ Error sending email: {str(e)}")
    print("\n  🔍 Troubleshooting:")
    
    error_str = str(e).lower()
    
    if 'authentication' in error_str or '535' in error_str or 'badcredentials' in error_str:
        print("     ⚠️  Authentication failed!")
        print("        - Check that EMAIL_HOST_USER is 'apikey' (literal)")
        print("        - Verify your SendGrid API key is correct")
        print("        - Ensure API key has 'Mail Send' permissions")
    elif 'connection' in error_str or 'timeout' in error_str:
        print("     ⚠️  Connection failed!")
        print("        - Check EMAIL_HOST is 'smtp.sendgrid.net'")
        print("        - Verify EMAIL_PORT is 587")
        print("        - Check your internet connection")
    elif '550' in error_str or 'quota' in error_str or 'limit' in error_str:
        print("     ⚠️  Sending limit exceeded!")
        print("        - Check SendGrid account limits")
        print("        - Verify domain is fully verified")
    elif 'domain' in error_str or 'verified' in error_str:
        print("     ⚠️  Domain verification issue!")
        print("        - Ensure domain is verified in SendGrid")
        print("        - Check DNS records are properly configured")
        print("        - Wait for DNS propagation (can take up to 48 hours)")
    else:
        print(f"     ⚠️  Unexpected error: {type(e).__name__}")
        import traceback
        traceback.print_exc()
    
    print("\n  📋 SendGrid Checklist:")
    print("     [ ] Domain is verified in SendGrid")
    print("     [ ] DNS records are added and verified")
    print("     [ ] API key has 'Mail Send' permission")
    print("     [ ] API key is correct (starts with SG.)")
    print("     [ ] EMAIL_HOST_USER is set to 'apikey'")
    print("     [ ] DEFAULT_FROM_EMAIL uses your verified domain")

print("\n" + "=" * 60)

