#!/bin/bash

# Render Database Initialization Script
# Run this manually on Render or add to your service startup

echo "🗄️ Initializing database on Render..."

# Set environment for Django
export DJANGO_SETTINGS_MODULE="procure_to_pay.settings"

# Run migrations
echo "🔄 Running database migrations..."
python manage.py migrate --verbosity=2

if [ $? -eq 0 ]; then
    echo "✅ Migrations completed successfully!"
else
    echo "❌ Migrations failed!"
    exit 1
fi

# Check if admin user exists, create if not
echo "👤 Setting up admin user..."
python manage.py shell << EOF
from django.contrib.auth.models import User
import os

admin_email = os.environ.get('ADMIN_EMAIL', 'admin@procure-to-pay.com')
admin_password = os.environ.get('ADMIN_PASSWORD', 'admin123')

if not User.objects.filter(is_superuser=True).exists():
    User.objects.create_superuser(
        username='admin',
        email=admin_email,
        password=admin_password
    )
    print(f"✅ Admin user created: {admin_email}")
    print("⚠️ Please change the admin password!")
else:
    print("✅ Admin user already exists")
EOF

echo "🎉 Database initialization completed!"
echo "🌐 Your API is ready at: https://procure-to-pay-server.onrender.com/"
echo "📖 API docs at: https://procure-to-pay-server.onrender.com/api/docs/"
echo "🔧 Admin panel at: https://procure-to-pay-server.onrender.com/admin/"