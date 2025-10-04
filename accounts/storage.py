"""
Custom storage backend for handling media files on Render
Uses Imgur API for free image hosting
"""
import requests
import base64
from django.core.files.storage import Storage
from django.core.files.base import ContentFile
from django.conf import settings
import os


class ImgurStorage(Storage):
    """
    Custom storage that uploads images to Imgur and stores the URL in the database
    """
    
    def __init__(self):
        self.imgur_client_id = getattr(settings, 'IMGUR_CLIENT_ID', None)
        self.base_url = 'https://api.imgur.com/3/'
    
    def _open(self, name, mode='rb'):
        # For reading, we'll fetch from the URL
        if hasattr(self, '_urls') and name in self._urls:
            response = requests.get(self._urls[name])
            return ContentFile(response.content)
        return ContentFile(b'')
    
    def _save(self, name, content):
        if not self.imgur_client_id:
            # Fallback to local storage if no Imgur client ID
            return self._save_local(name, content)
        
        try:
            # Upload to Imgur
            url = self._upload_to_imgur(content)
            if url:
                # Store the URL in a way that we can retrieve it
                # We'll modify the name to include the URL
                return f"imgur:{url}"
            else:
                return self._save_local(name, content)
        except Exception as e:
            print(f"Imgur upload failed: {e}")
            return self._save_local(name, content)
    
    def _upload_to_imgur(self, content):
        """Upload image to Imgur and return the URL"""
        try:
            # Convert file to base64
            content.seek(0)
            image_data = base64.b64encode(content.read()).decode('utf-8')
            
            headers = {
                'Authorization': f'Client-ID {self.imgur_client_id}',
                'Content-Type': 'application/json'
            }
            
            data = {
                'image': image_data,
                'type': 'base64'
            }
            
            response = requests.post(
                f'{self.base_url}image',
                headers=headers,
                json=data
            )
            
            if response.status_code == 200:
                result = response.json()
                return result['data']['link']
            else:
                print(f"Imgur API error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"Error uploading to Imgur: {e}")
            return None
    
    def _save_local(self, name, content):
        """Fallback to local storage"""
        # Create media directory if it doesn't exist
        media_dir = os.path.join(settings.BASE_DIR, 'media')
        os.makedirs(media_dir, exist_ok=True)
        
        # Save file locally
        file_path = os.path.join(media_dir, name)
        with open(file_path, 'wb') as f:
            for chunk in content.chunks():
                f.write(chunk)
        
        return name
    
    def url(self, name):
        """Return the URL for the file"""
        if name.startswith('imgur:'):
            # Extract the actual URL from our custom format
            return name[6:]  # Remove 'imgur:' prefix
        else:
            # Local file
            return f"{settings.MEDIA_URL}{name}"
    
    def exists(self, name):
        """Check if file exists"""
        if name.startswith('imgur:'):
            # For Imgur URLs, we assume they exist
            return True
        else:
            # Check local file
            file_path = os.path.join(settings.BASE_DIR, 'media', name)
            return os.path.exists(file_path)
    
    def delete(self, name):
        """Delete the file"""
        if not name.startswith('imgur:'):
            # Only delete local files
            file_path = os.path.join(settings.BASE_DIR, 'media', name)
            if os.path.exists(file_path):
                os.remove(file_path)
    
    def size(self, name):
        """Get file size"""
        if name.startswith('imgur:'):
            # For Imgur files, we can't easily get size
            return 0
        else:
            file_path = os.path.join(settings.BASE_DIR, 'media', name)
            if os.path.exists(file_path):
                return os.path.getsize(file_path)
            return 0
