# Cloudinary Setup for MjoloBid on Render (Easier Alternative)

## Overview
Cloudinary is easier to set up than AWS S3 and provides excellent image optimization features.

## Step 1: Create Cloudinary Account

1. Go to [Cloudinary](https://cloudinary.com/)
2. Sign up for a free account
3. Go to your dashboard
4. Note down your:
   - Cloud name
   - API Key
   - API Secret

## Step 2: Update Requirements

The requirements.txt has been updated to include Cloudinary support.

## Step 3: Configure Render Environment Variables

In your Render dashboard, go to your service → Environment tab and add these variables:

```
USE_CLOUDINARY=True
CLOUDINARY_CLOUD_NAME=your_cloud_name_here
CLOUDINARY_API_KEY=your_api_key_here
CLOUDINARY_API_SECRET=your_api_secret_here
```

## Step 4: Deploy

1. Commit and push your changes
2. Render will automatically redeploy
3. Profile pictures will now be stored in Cloudinary and persist across deployments

## Benefits of Cloudinary

- ✅ Easy setup (no complex AWS configuration)
- ✅ Automatic image optimization
- ✅ Free tier with generous limits
- ✅ Built-in image transformations
- ✅ CDN delivery for fast loading
- ✅ Automatic format conversion (WebP, AVIF)

## Testing

After deployment:
1. Create a new account
2. Upload a profile picture
3. Check that it displays correctly
4. Restart your Render service
5. Verify the profile picture still displays (it should persist now)
