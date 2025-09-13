from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'
    
    def ready(self):
        """Called when the app is ready"""
        # Only run in production (Render)
        if not self._is_development():
            self._create_superuser_if_needed()
    
    def _is_development(self):
        """Check if we're in development mode"""
        import os
        return os.environ.get('DEBUG', 'False').lower() == 'true'
    
    def _create_superuser_if_needed(self):
        """Create superuser if it doesn't exist"""
        try:
            from django.contrib.auth import get_user_model
            
            User = get_user_model()
            username = "tron"
            email = "tronmapzy@gmail.com"
            password = "admin123"
            
            if not User.objects.filter(username=username).exists():
                user = User.objects.create_superuser(
                    username=username,
                    email=email,
                    password=password
                )
                print(f"✅ Superuser '{username}' created successfully!")
            else:
                print(f"✅ Superuser '{username}' already exists!")
                
        except Exception as e:
            print(f"❌ Error creating superuser: {e}")