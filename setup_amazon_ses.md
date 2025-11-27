# Amazon SES Setup Guide (No Phone Verification)

## Step 1: Create AWS Account
1. Go to https://aws.amazon.com/
2. Click "Create an AWS Account"
3. Use your email (no phone verification required for basic setup)
4. Choose "Personal" account type
5. Complete registration

## Step 2: Set up Amazon SES
1. Log into AWS Console
2. Search for "SES" (Simple Email Service)
3. Choose your region (us-east-1 recommended)
4. Click "Create Identity"
5. Choose "Email Address"
6. Enter your email address
7. Verify your email address (check inbox)

## Step 3: Get SMTP Credentials
1. In SES Console, go to "SMTP Settings"
2. Click "Create SMTP Credentials"
3. Enter username (e.g., "mjolobid-smtp")
4. Download the credentials file
5. Note down:
   - SMTP Username
   - SMTP Password
   - Server Name (e.g., email-smtp.us-east-1.amazonaws.com)
   - Port: 587

## Step 4: Update Django Settings
Replace Gmail settings with:

```python
# Amazon SES Configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'email-smtp.us-east-1.amazonaws.com'  # Your SES region
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'YOUR_SMTP_USERNAME'
EMAIL_HOST_PASSWORD = 'YOUR_SMTP_PASSWORD'
DEFAULT_FROM_EMAIL = 'MjoloBid <your-verified-email@domain.com>'
```

## Step 5: Test
```bash
python manage.py test_mailgun --to-email your-email@example.com
```

## Benefits:
- ✅ No phone verification required
- ✅ Excellent deliverability
- ✅ Very cheap ($0.10 per 1,000 emails)
- ✅ Reliable service
- ✅ Easy Django integration

## Note:
Initially you'll be in "sandbox mode" - can only send to verified email addresses.
To send to any email, request production access (usually approved quickly).
