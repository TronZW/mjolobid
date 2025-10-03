# AWS S3 Setup for MjoloBid on Render

## Overview
This guide will help you set up AWS S3 for storing profile pictures and other media files on Render.

## Step 1: Create AWS S3 Bucket

1. Go to [AWS S3 Console](https://s3.console.aws.amazon.com/)
2. Click "Create bucket"
3. Choose a unique bucket name (e.g., `mjolobid-media-files`)
4. Select a region (e.g., `us-east-1`)
5. Uncheck "Block all public access" and acknowledge the warning
6. Click "Create bucket"

## Step 2: Configure Bucket Policy

1. Go to your bucket → Permissions tab
2. Scroll down to "Bucket policy"
3. Add this policy (replace `YOUR_BUCKET_NAME` with your actual bucket name):

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "PublicReadGetObject",
            "Effect": "Allow",
            "Principal": "*",
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::YOUR_BUCKET_NAME/*"
        }
    ]
}
```

## Step 3: Create IAM User

1. Go to [AWS IAM Console](https://console.aws.amazon.com/iam/)
2. Click "Users" → "Create user"
3. Username: `mjolobid-s3-user`
4. Attach policies directly → "Create policy"
5. Use this policy (replace `YOUR_BUCKET_NAME`):

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:PutObject",
                "s3:DeleteObject"
            ],
            "Resource": "arn:aws:s3:::YOUR_BUCKET_NAME/*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "s3:ListBucket"
            ],
            "Resource": "arn:aws:s3:::YOUR_BUCKET_NAME"
        }
    ]
}
```

6. Name the policy: `MjoloBidS3Policy`
7. Create the policy
8. Attach it to your user
9. Go to "Security credentials" tab → "Create access key"
10. Choose "Application running outside AWS"
11. Save the Access Key ID and Secret Access Key

## Step 4: Configure Render Environment Variables

In your Render dashboard, go to your service → Environment tab and add these variables:

```
USE_S3=True
AWS_ACCESS_KEY_ID=your_access_key_id_here
AWS_SECRET_ACCESS_KEY=your_secret_access_key_here
AWS_STORAGE_BUCKET_NAME=your_bucket_name_here
AWS_S3_REGION_NAME=us-east-1
```

## Step 5: Deploy

1. Commit and push your changes
2. Render will automatically redeploy
3. Profile pictures will now be stored in S3 and persist across deployments

## Alternative: Use Cloudinary (Easier Setup)

If you prefer an easier setup, you can use Cloudinary instead:

1. Sign up at [Cloudinary](https://cloudinary.com/)
2. Get your cloud name, API key, and API secret
3. Add to requirements.txt: `cloudinary==1.36.0`
4. Add to INSTALLED_APPS: `'cloudinary_storage', 'cloudinary'`
5. Add environment variables:
   ```
   CLOUDINARY_CLOUD_NAME=your_cloud_name
   CLOUDINARY_API_KEY=your_api_key
   CLOUDINARY_API_SECRET=your_api_secret
   ```

## Testing

After deployment:
1. Create a new account
2. Upload a profile picture
3. Check that it displays correctly
4. Restart your Render service
5. Verify the profile picture still displays (it should persist now)
