"""
ASGI config for hostel_project project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os
import django
from django.core.asgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hostel_project.settings')

# Run database initialization (migrations + seeding)
try:
    django.setup()
    from django.core.management import call_command
    from django.contrib.auth import get_user_model
    
    # 1. Run migrations automatically
    print("Auto-running migrations...")
    call_command('migrate', interactive=False)
    
    # 2. Seed database if admin user doesn't exist
    User = get_user_model()
    if not User.objects.filter(role='admin').exists():
        print("Admin user not found. Seeding initial data...")
        import seed_data
        seed_data.seed()
except Exception as e:
    print(f"Database initialization failed: {e}")

application = get_wsgi_application()
