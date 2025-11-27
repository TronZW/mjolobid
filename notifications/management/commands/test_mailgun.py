from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Test Mailgun email configuration'

    def add_arguments(self, parser):
        parser.add_argument(
            '--to-email',
            type=str,
            help='Email address to send test email to',
            required=True
        )

    def handle(self, *args, **options):
        to_email = options['to_email']
        
        self.stdout.write('Testing Mailgun email configuration...')
        self.stdout.write(f'EMAIL_HOST: {settings.EMAIL_HOST}')
        self.stdout.write(f'EMAIL_PORT: {settings.EMAIL_PORT}')
        self.stdout.write(f'EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}')
        self.stdout.write(f'EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}')
        self.stdout.write(f'DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}')
        
        try:
            send_mail(
                subject='MjoloBid - Mailgun Test Email',
                message='This is a test email from MjoloBid using Mailgun SMTP.\n\nIf you receive this, Mailgun is working correctly!',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[to_email],
                fail_silently=False,
            )
            
            self.stdout.write(
                self.style.SUCCESS(f'✅ Test email sent successfully to {to_email}')
            )
            self.stdout.write('Check your inbox (and spam folder) for the test email.')
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Failed to send test email: {str(e)}')
            )
            self.stdout.write('\nTroubleshooting tips:')
            self.stdout.write('1. Verify your Mailgun SMTP credentials')
            self.stdout.write('2. Check that your Mailgun domain is verified')
            self.stdout.write('3. Ensure EMAIL_HOST_USER and EMAIL_HOST_PASSWORD are correct')
            self.stdout.write('4. Make sure you\'re using the sandbox domain for testing')
