# Wetail Core

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![Django](https://img.shields.io/badge/django-4.2-green)](https://www.djangoproject.com/)

**Wetail Core** is an open-source e-commerce platform foundation built on Django. It provides essential marketplace functionality for building custom e-commerce solutions.

## Features

### Core Functionality
- 🛒 **Marketplace Basics** - Product listings, categories, search
- 👤 **User Management** - Authentication, profiles, roles
- 💳 **Checkout** - Shopping cart, order processing
- 📦 **Shipping** - Shipping method integration
- 💰 **Payments** - Stripe integration
- 🔔 **Notifications** - Email and in-app notifications

### Developer Experience
- 🔧 **Modular Architecture** - Easy to extend and customize
- 🏥 **Health Checks** - Kubernetes-ready liveness/readiness probes
- 🔒 **Security Middleware** - Rate limiting, security headers
- 📊 **Caching Utilities** - Performance optimization helpers
- ⚡ **Lazy Loading** - Avoid circular import issues

## Installation

```bash
pip install wetail-core
```

## Quick Start

1. Add to your Django `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    # Django built-ins
    'django.contrib.admin',
    'django.contrib.auth',
    # ...
    
    # Wetail Core
    'wetail_core.core',
    'wetail_core.marketplace',
    'wetail_core.checkout',
    'wetail_core.user',
]
```

2. Add middleware:

```python
MIDDLEWARE = [
    # ...
    'wetail_core.core.middleware.SecurityHeadersMiddleware',
    'wetail_core.core.middleware.RateLimitMiddleware',
]
```

3. Include URLs:

```python
from django.urls import path, include

urlpatterns = [
    path('health/', include('wetail_core.core.health.urls')),
    path('api/', include('wetail_core.marketplace.urls')),
    # ...
]
```

4. Run migrations:

```bash
python manage.py migrate
```

## Enterprise Features

For advanced features, check out **[wetail-enterprise](https://wetail.co/enterprise)**:

| Feature | Core | Enterprise |
|---------|:----:|:----------:|
| Basic Marketplace | ✅ | ✅ |
| User Management | ✅ | ✅ |
| Checkout & Payments | ✅ | ✅ |
| Health Checks | ✅ | ✅ |
| **Advanced Commerce** | ❌ | ✅ |
| **AI-Powered Features** | ❌ | ✅ |
| **Business Intelligence** | ❌ | ✅ |
| **Automation Suite** | ❌ | ✅ |
| **Advanced Analytics** | ❌ | ✅ |
| **Priority Support** | ❌ | ✅ |

## Documentation

- [Getting Started Guide](https://docs.wetail.co/core/getting-started)
- [API Reference](https://docs.wetail.co/core/api)
- [Configuration](https://docs.wetail.co/core/configuration)
- [Deployment Guide](https://docs.wetail.co/core/deployment)

## Development

```bash
# Clone the repository
git clone https://github.com/abarnes1205/Wetail_Mona_Lisa.git
cd Wetail_Mona_Lisa

# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black wetail_core
isort wetail_core
```

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## Support

- 📚 [Documentation](https://docs.wetail.co/core)
- 💬 [GitHub Discussions](https://github.com/abarnes1205/Wetail_Mona_Lisa/discussions)
- 🐛 [Issue Tracker](https://github.com/abarnes1205/Wetail_Mona_Lisa/issues)
- 📧 [Email Support](mailto:altonbarnes7@gmail.com)

---

Made with ❤️ by Alton Barnes / [Wetail Technologies](https://wetail.co)
