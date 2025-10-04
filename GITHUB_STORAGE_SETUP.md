# GitHub Storage Setup for Render

This guide shows how to set up persistent image storage using GitHub as a free image hosting service.

## Why GitHub Storage?

- **Free**: GitHub offers unlimited storage for public repositories
- **Simple Setup**: No complex cloud storage configurations
- **Persistent**: Images will never be lost
- **Fast**: GitHub's CDN provides fast image loading
- **Reliable**: GitHub has excellent uptime

## Setup Steps

### Step 1: Create a GitHub Repository for Images

1. Go to [GitHub](https://github.com) and create a new repository
2. Name it something like `mjolobid-images` or `your-app-images`
3. Make it **Public** (required for free access)
4. Don't initialize with README, .gitignore, or license
5. Click "Create repository"

### Step 2: Create a GitHub Personal Access Token

1. Go to GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Click "Generate new token (classic)"
3. Give it a name like "MjoloBid Image Upload"
4. Select scopes:
   - ✅ `repo` (Full control of private repositories)
   - ✅ `public_repo` (Access public repositories)
5. Click "Generate token"
6. **Copy the token immediately** (you won't see it again)

### Step 3: Configure Render Environment Variables

1. Go to your Render dashboard and select your `MjoloBid` service
2. Navigate to the "Environment" section
3. Add the following environment variables:

   - `USE_GITHUB_STORAGE`: `True`
   - `GITHUB_TOKEN`: `your_github_token_here` (paste the token from Step 2)
   - `GITHUB_REPO`: `your_username/mjolobid-images` (replace with your actual repo)

### Step 4: Deploy Your Application

1. Ensure you have committed and pushed the latest changes to your GitHub repository
2. Render should automatically detect the changes and redeploy your service
3. If not, manually trigger a deploy from the Render dashboard

## Example Configuration

If your GitHub username is `john` and you created a repository called `mjolobid-images`, your environment variables would be:

```
USE_GITHUB_STORAGE=True
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
GITHUB_REPO=john/mjolobid-images
```

## How It Works

1. When a user uploads a profile picture, it gets uploaded to your GitHub repository
2. The image is stored in the `profile_pics/` folder
3. GitHub provides a direct URL to access the image
4. The URL is stored in your database
5. Images are served directly from GitHub's CDN

## Benefits

- ✅ **Free**: No cost for storage or bandwidth
- ✅ **Persistent**: Images never disappear
- ✅ **Fast**: Served from GitHub's global CDN
- ✅ **Simple**: No complex cloud storage setup
- ✅ **Reliable**: GitHub's excellent uptime

## Testing

After deployment:

1. **Create a new user account** on your Render-deployed application
2. **Upload a profile picture** during registration or profile setup
3. **Verify that the profile picture displays correctly** on the profile page
4. **Check your GitHub repository** - you should see the uploaded images in the `profile_pics/` folder

## Troubleshooting

- **Images not uploading**: Check that your GitHub token has the correct permissions
- **Images not displaying**: Verify the repository is public and the URL format is correct
- **Permission errors**: Ensure your GitHub token has `repo` and `public_repo` scopes

This setup provides a robust, free solution for persistent image storage on Render!
