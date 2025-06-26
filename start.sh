#!/bin/bash

# Exit on any error
set -e

echo "🔧 Running makemigrations..."
python manage.py makemigrations

echo "🔧 Running migrate..."
python manage.py migrate

echo "👤 Creating default superuser (if not exists)..."
python manage.py shell << END
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@gamil.com', 'admin123')
    print("✅ Superuser created.")
else:
    print("⚠️ Superuser already exists.")
END

echo "🚀 Starting Gunicorn..."
gunicorn backend.wsgi:application
