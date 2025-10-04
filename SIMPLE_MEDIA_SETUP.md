# Simple Media Storage Setup for Render

## The Problem
Render's file system is ephemeral - files get deleted when the container restarts. This is why your profile pictures disappear.

## Simple Solutions

### Option 1: Use Imgur (Recommended - 2 minutes setup)

1. **Go to [Imgur API](https://api.imgur.com/oauth2/addclient)**
2. **Create a new application**:
   - Application name: `MjoloBid`
   - Authorization type: `Anonymous usage without user authorization`
   - Click "Submit"
3. **Copy the Client ID** (not the secret)
4. **Add to Render environment variables**:
   ```
   USE_IMGUR=True
   IMGUR_CLIENT_ID=your_client_id_here
   ```
5. **Deploy** - That's it!

**Benefits:**
- ✅ Free (no cost)
- ✅ No complex setup
- ✅ Images persist forever
- ✅ Fast CDN delivery
- ✅ Automatic image optimization

### Option 2: Accept Temporary Storage (No Setup Required)

If you don't want to set up anything, the app will work with local storage, but:
- ❌ Profile pictures will disappear when Render restarts
- ✅ Everything else works normally
- ✅ Good for development/testing

Just deploy without any environment variables.

### Option 3: Use GitHub as File Storage

1. **Create a GitHub repository** for storing images
2. **Get a GitHub Personal Access Token**
3. **Add environment variables**:
   ```
   USE_GITHUB=True
   GITHUB_TOKEN=your_token_here
   GITHUB_REPO=your_username/your_repo_name
   ```

## Testing

After setup:
1. Deploy to Render
2. Create a new account
3. Upload a profile picture
4. Restart your Render service
5. Check if the profile picture still shows

## Troubleshooting

**If Imgur doesn't work:**
- Check that your Client ID is correct
- Make sure you're using the Client ID, not the Client Secret
- Check Render logs for any error messages

**If you want to switch back to local storage:**
- Remove the environment variables
- Redeploy

## Why This Approach?

- **Simple**: No complex AWS setup
- **Free**: Imgur is free for reasonable usage
- **Reliable**: Imgur is a stable service
- **Fast**: Images load quickly via CDN
- **Fallback**: If Imgur fails, it falls back to local storage
