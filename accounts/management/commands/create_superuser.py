from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = 'Create a superuser with predefined credentials'

    def handle(self, *args, **options):
        User = get_user_model()
        
        # Superuser credentials
        username = "tron"
        email = "tronmapzy@gmail.com"
        password = "admin123"
        
        try:
            # Check if superuser already exists
            if User.objects.filter(username=username).exists():
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Superuser "{username}" already exists!')
                )
                return
            
            # Create superuser
            user = User.objects.create_superuser(
                username=username,
                email=email,
                password=password
            )
            
            self.stdout.write(
                self.style.SUCCESS('✅ Superuser created successfully!')
            )
            self.stdout.write(f'Username: {username}')
            self.stdout.write(f'Email: {email}')
            self.stdout.write(f'Password: {password}')
            self.stdout.write('\n🔗 Admin Panel: https://mjolobid.onrender.com/admin/')
            self.stdout.write('⚠️  Remember to change the password after first login!')
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error creating superuser: {e}')
            )
