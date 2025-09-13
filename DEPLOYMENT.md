# 🚀 MjoloBid Deployment Guide

This guide will help you deploy your MjoloBid application to Railway for free.

## 📋 Prerequisites

1. **GitHub Account** - Your code needs to be on GitHub
2. **Railway Account** - Sign up at [railway.app](https://railway.app)
3. **Stripe Account** - For payment processing
4. **Email Service** - Gmail or similar for sending emails

## 🎯 Step 1: Prepare Your Code

### 1.1 Push to GitHub
```bash
git add .
git commit -m "Prepare for deployment"
git push origin main
```

### 1.2 Remove Debug Code
Before deploying, remove the debug code we added:

```bash
# Remove debug prints from bids/views.py
# Remove debug panel from templates/bids/browse_bids.html
```

## 🚂 Step 2: Deploy to Railway

### 2.1 Create Railway Project
1. Go to [railway.app](https://railway.app)
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Choose your MjoloBid repository
5. Click "Deploy Now"

### 2.2 Add PostgreSQL Database
1. In your Railway project, click "New"
2. Select "Database" → "PostgreSQL"
3. Wait for it to provision
4. Copy the connection details

### 2.3 Add Redis (Optional)
1. Click "New" → "Database" → "Redis"
2. Copy the Redis URL

## ⚙️ Step 3: Configure Environment Variables

In Railway dashboard, go to your service → Variables tab and add:

### Required Variables:
```
SECRET_KEY=your-very-secure-secret-key-here
DEBUG=False
DATABASE_NAME=railway
DATABASE_USER=postgres
DATABASE_PASSWORD=your-postgres-password
DATABASE_HOST=your-postgres-host
DATABASE_PORT=5432
REDIS_URL=redis://your-redis-url
STRIPE_PUBLISHABLE_KEY=pk_test_your-stripe-key
STRIPE_SECRET_KEY=sk_test_your-stripe-secret
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

### Generate Secret Key:
```python
from django.core.management.utils import get_random_secret_key
print(get_random_secret_key())
```

## 🔧 Step 4: Configure Build Settings

Railway will automatically detect your Python app, but you can customize:

1. Go to your service → Settings
2. Set **Build Command**: `pip install -r requirements.txt`
3. Set **Start Command**: `gunicorn mjolobid.wsgi:application --bind 0.0.0.0:$PORT`

## 🗄️ Step 5: Database Setup

### 5.1 Run Migrations
Railway will automatically run migrations, but you can also do it manually:

1. Go to your service → Deployments
2. Click on the latest deployment
3. Go to "Logs" tab
4. You should see migration output

### 5.2 Create Superuser
You'll need to create a superuser for admin access:

1. Go to your service → Deployments
2. Click "View Logs"
3. Run: `python manage.py createsuperuser`

## 🌐 Step 6: Configure Domain

### 6.1 Get Your Railway URL
Railway provides a free subdomain like: `your-app-name.railway.app`

### 6.2 Custom Domain (Optional)
1. Go to your service → Settings → Domains
2. Add your custom domain
3. Update DNS records as instructed

## 📧 Step 7: Email Configuration

### 7.1 Gmail Setup
1. Enable 2-factor authentication
2. Generate an App Password
3. Use the app password in `EMAIL_HOST_PASSWORD`

### 7.2 Alternative Email Services
- **SendGrid** (Free tier: 100 emails/day)
- **Mailgun** (Free tier: 5,000 emails/month)
- **Amazon SES** (Free tier: 62,000 emails/month)

## 💳 Step 8: Stripe Configuration

### 8.1 Get Stripe Keys
1. Go to [stripe.com](https://stripe.com)
2. Get your test keys from Dashboard → Developers → API keys
3. Add them to Railway environment variables

### 8.2 Webhook Setup
1. In Stripe Dashboard → Webhooks
2. Add endpoint: `https://your-app.railway.app/payments/webhook/`
3. Select events: `checkout.session.completed`, `payment_intent.succeeded`
4. Copy webhook secret to Railway

## 🔍 Step 9: Testing Your Deployment

### 9.1 Basic Tests
1. Visit your Railway URL
2. Test user registration
3. Test bid posting
4. Test payment flow (use Stripe test cards)

### 9.2 Test Cards (Stripe)
- **Success**: 4242 4242 4242 4242
- **Decline**: 4000 0000 0000 0002
- **3D Secure**: 4000 0025 0000 3155

## 🚨 Troubleshooting

### Common Issues:

#### 1. Build Fails
- Check `requirements.txt` for all dependencies
- Ensure Python version is compatible
- Check build logs in Railway dashboard

#### 2. Database Connection Error
- Verify database credentials
- Check if database is running
- Ensure migrations are applied

#### 3. Static Files Not Loading
- Check `STATIC_ROOT` setting
- Ensure `collectstatic` ran successfully
- Verify WhiteNoise configuration

#### 4. Email Not Sending
- Check email credentials
- Verify SMTP settings
- Test with a simple email first

## 📊 Monitoring

### Railway Dashboard
- Monitor resource usage
- Check deployment logs
- View error logs

### Django Admin
- Access at: `https://your-app.railway.app/admin/`
- Monitor user registrations
- Check bid activity

## 💰 Cost Management

### Railway Free Tier Limits:
- $5 credit monthly
- 512MB RAM
- 1GB storage
- 100GB bandwidth

### Optimization Tips:
1. Use efficient database queries
2. Optimize static files
3. Monitor resource usage
4. Consider upgrading if needed

## 🔄 Updates and Maintenance

### Deploying Updates:
1. Push changes to GitHub
2. Railway auto-deploys
3. Monitor deployment logs
4. Test functionality

### Database Backups:
Railway provides automatic backups, but you can also:
1. Export data manually
2. Use Django's dumpdata command
3. Set up automated backups

## 🎉 You're Live!

Your MjoloBid application should now be running on Railway! 

### Next Steps:
1. Test all functionality
2. Set up monitoring
3. Configure custom domain
4. Set up SSL certificates
5. Plan for scaling

## 📞 Support

If you encounter issues:
1. Check Railway documentation
2. Review Django deployment guides
3. Check application logs
4. Test locally first

Happy deploying! 🚀
