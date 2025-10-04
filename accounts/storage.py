import base64
import requests
from django.core.files.storage import Storage
from django.conf import settings
from django.core.files.base import ContentFile
import os
import uuid
from datetime import datetime

class GitHubStorage(Storage):
    """
    A custom storage backend for Django that uploads files to GitHub.
    Requires GITHUB_TOKEN and GITHUB_REPO in settings.
    """
    
    def _save(self, name, content):
        """
        Save a new file to GitHub.
        """
        if not settings.GITHUB_TOKEN or not settings.GITHUB_REPO:
            raise Exception("GITHUB_TOKEN and GITHUB_REPO must be set in settings.")

        # Generate a unique filename
        file_extension = os.path.splitext(name)[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        github_path = f"profile_pics/{unique_filename}"

        # Read the file content
        content.seek(0)
        file_content = content.read()
        
        # Encode to base64
        encoded_content = base64.b64encode(file_content).decode('utf-8')

        # GitHub API endpoint
        url = f"https://api.github.com/repos/{settings.GITHUB_REPO}/contents/{github_path}"
        
        headers = {
            "Authorization": f"token {settings.GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json"
        }

        # Prepare the data
        data = {
            "message": f"Upload profile picture - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "content": encoded_content
        }

        # Upload to GitHub
        response = requests.put(url, headers=headers, json=data)
        
        if response.status_code == 201:
            # Return the GitHub raw URL
            return f"https://raw.githubusercontent.com/{settings.GITHUB_REPO}/main/{github_path}"
        else:
            raise Exception(f"GitHub upload failed: {response.status_code} - {response.text}")

    def _open(self, name, mode='rb'):
        """
        Open a file from GitHub.
        This method is typically not used for remote storage where URLs are directly accessed.
        """
        raise NotImplementedError("GitHubStorage does not support opening files directly.")

    def delete(self, name):
        """
        Delete a file from GitHub.
        This requires the file SHA which we don't store, so it's not implemented for simplicity.
        """
        pass  # Not implemented for simplicity

    def exists(self, name):
        """
        Check if a file exists on GitHub.
        This is a simplified check and might not be fully accurate.
        """
        return bool(name)  # If name (GitHub URL) exists, assume it exists

    def url(self, name):
        """
        Return the URL to access the file directly.
        For GitHub, the 'name' stored is already the URL.
        """
        return name

    def get_valid_name(self, name):
        """
        Return a filename that's safe to use.
        For GitHub, we're storing the URL, so we don't need to validate the name.
        """
        return name

    def get_available_name(self, name, max_length=None):
        """
        Return a filename that's available.
        For GitHub, we're storing the URL, so we don't need to check for availability.
        """
        return name
