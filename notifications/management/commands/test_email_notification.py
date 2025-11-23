"""
Management command to test email notifications
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from notifications.utils import send_notification

User = get_user_model()


class Command(BaseCommand):
    help = 'Test email notification sending'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            help='Username to send test email to',
            default=None,
        )
        parser.add_argument(
            '--type',
            type=str,
            choices=['NEW_MESSAGE', 'OFFER_BID', 'OFFER_ACCEPTED', 'BID_ACCEPTED'],
            default='NEW_MESSAGE',
            help='Notification type to test',
        )

    def handle(self, *args, **options):
        username = options['username']
        notification_type = options['type']
        
        if not username:
            # Get first user with email
            user = User.objects.filter(email__isnull=False).exclude(email='').first()
            if not user:
                self.stdout.write(self.style.ERROR('No users with email addresses found. Please specify --username'))
                return
        else:
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'User "{username}" not found'))
                return
        
        if not user.email:
            self.stdout.write(self.style.ERROR(f'User "{username}" has no email address'))
            return
        
        self.stdout.write(self.style.SUCCESS(f'\nSending test email notification to {user.username} ({user.email})'))
        self.stdout.write(f'Notification type: {notification_type}\n')
        
        # Send test notification
        notification = send_notification(
            user=user,
            title='Test Email Notification',
            message='This is a test email notification. If you receive this email, email notifications are working correctly!',
            notification_type=notification_type,
            related_object_type='test'
        )
        
        self.stdout.write(self.style.SUCCESS(f'\n✓ Notification created: {notification.id}'))
        self.stdout.write(f'Check your console output above for email sending status.')
        self.stdout.write(f'If using console email backend, the email will be printed above.\n')

