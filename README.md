# 🎯 MjoloBid - Social Event Companion Platform

A Django-based web application that connects people for social events through a bidding system. Users can post bids for social events and find companions to join them.

## 🌟 Features

- **User Authentication**: Registration and login system with user profiles
- **Bid Management**: Post, browse, and manage social event bids
- **Real-time Notifications**: WebSocket-based notifications for new bids
- **Payment Integration**: Stripe integration for subscription payments
- **Review System**: Rate and review companions after events
- **Location-based Matching**: Find companions based on location
- **Admin Dashboard**: Comprehensive admin panel for platform management

## 🚀 Quick Start

### Prerequisites
- Python 3.12+
- Redis (for real-time features)
- PostgreSQL (for production)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/TronZW/mjolobid.git
   cd mjolobid
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp env.example .env
   # Edit .env with your configuration
   ```

5. **Run migrations**
   ```bash
   python manage.py migrate
   ```

6. **Create superuser**
   ```bash
   python manage.py createsuperuser
   ```

7. **Load sample data**
   ```bash
   python manage.py loaddata sample_data.json
   ```

8. **Start the development server**
   ```bash
   python run_server.py
   ```

## 🏗️ Project Structure

```
mjolobid/
├── accounts/          # User authentication and profiles
├── bids/             # Bid management and browsing
├── payments/         # Stripe payment integration
├── notifications/    # Real-time notifications
├── admin_dashboard/  # Admin panel
├── templates/        # HTML templates
├── static/          # CSS, JS, and images
├── media/           # User uploaded files
└── mjolobid/        # Django project settings
```

## 🛠️ Technology Stack

- **Backend**: Django 4.2, Django REST Framework
- **Database**: SQLite (development), PostgreSQL (production)
- **Real-time**: Django Channels, Redis
- **Frontend**: HTML, CSS (Tailwind), JavaScript
- **Payments**: Stripe
- **Deployment**: Railway, Gunicorn
- **Task Queue**: Celery

## 📱 User Types

### Male Users (Bid Posters)
- Post bids for social events
- Set bid amounts for companions
- Manage their posted bids
- Review accepted companions

### Female Users (Companions)
- Browse available bids
- Accept bids they're interested in
- Manage their accepted bids
- Review bid posters

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `SECRET_KEY` | Django secret key | Yes |
| `DEBUG` | Debug mode | Yes |
| `DATABASE_URL` | Database connection string | Yes |
| `REDIS_URL` | Redis connection string | Yes |
| `STRIPE_PUBLISHABLE_KEY` | Stripe publishable key | Yes |
| `STRIPE_SECRET_KEY` | Stripe secret key | Yes |
| `EMAIL_HOST_USER` | Email username | Yes |
| `EMAIL_HOST_PASSWORD` | Email password | Yes |

## 🚀 Deployment

This application is configured for easy deployment on Railway. See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed deployment instructions.

### Quick Deploy to Railway

1. Push your code to GitHub
2. Connect your GitHub repository to Railway
3. Add PostgreSQL and Redis services
4. Configure environment variables
5. Deploy!

## 📊 API Endpoints

### Authentication
- `POST /accounts/register/` - User registration
- `POST /accounts/login/` - User login
- `POST /accounts/logout/` - User logout

### Bids
- `GET /bids/` - Browse available bids
- `POST /bids/post/` - Post a new bid
- `GET /bids/<id>/` - Bid details
- `POST /bids/<id>/accept/` - Accept a bid

### Payments
- `POST /payments/create-checkout/` - Create Stripe checkout
- `POST /payments/webhook/` - Stripe webhook

## 🧪 Testing

```bash
# Run tests
python manage.py test

# Run with coverage
coverage run --source='.' manage.py test
coverage report
```

## 📈 Monitoring

- **Django Admin**: `/admin/`
- **API Documentation**: `/api/docs/`
- **Health Check**: `/health/`

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

If you encounter any issues:

1. Check the [Issues](https://github.com/TronZW/mjolobid/issues) page
2. Review the [DEPLOYMENT.md](DEPLOYMENT.md) troubleshooting section
3. Create a new issue with detailed information

## 🎉 Acknowledgments

- Django community for the excellent framework
- Tailwind CSS for the beautiful styling
- Stripe for payment processing
- Railway for hosting platform

---

**Made with ❤️ for connecting people through social events**