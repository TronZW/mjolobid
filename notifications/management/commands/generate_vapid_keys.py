"""
Management command to generate VAPID keys for web push notifications
"""
from django.core.management.base import BaseCommand
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.backends import default_backend
import base64


class Command(BaseCommand):
    help = 'Generate VAPID keys for web push notifications'

    def handle(self, *args, **options):
        # Generate private key
        private_key = ec.generate_private_key(ec.SECP256R1(), default_backend())
        public_key = private_key.public_key()
        
        # Get private and public numbers
        private_numbers = private_key.private_numbers()
        public_numbers = public_key.public_numbers()
        
        # Encode private key (32 bytes)
        private_bytes = private_numbers.private_value.to_bytes(32, 'big')
        private_key_b64 = base64.urlsafe_b64encode(private_bytes).decode().rstrip('=')
        
        # Encode public key (65 bytes: 0x04 + 32 bytes x + 32 bytes y)
        public_bytes = bytes([0x04]) + public_numbers.x.to_bytes(32, 'big') + public_numbers.y.to_bytes(32, 'big')
        public_key_b64 = base64.urlsafe_b64encode(public_bytes).decode().rstrip('=')
        
        self.stdout.write(self.style.SUCCESS('\n=== VAPID Keys Generated ===\n'))
        self.stdout.write(f'WEBPUSH_VAPID_PUBLIC_KEY={public_key_b64}')
        self.stdout.write(f'WEBPUSH_VAPID_PRIVATE_KEY={private_key_b64}')
        self.stdout.write(f'WEBPUSH_VAPID_CONTACT_EMAIL=support@mjolobid.com')
        self.stdout.write(self.style.SUCCESS('\nAdd these to your .env file or environment variables.\n'))

