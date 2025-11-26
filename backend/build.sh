#!/bin/bash

# Render build script for Django
# This script runs during the build process on Render

echo "🚀 Starting Render build process..."

# Install system dependencies for OCR
echo "📦 Installing system dependencies..."
apt-get update
apt-get install -y tesseract-ocr
apt-get install -y libtesseract-dev

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Collect static files
echo "📁 Collecting static files..."
python manage.py collectstatic --noinput

# Run database migrations
echo "🗄️ Running database migrations..."
python manage.py migrate --verbosity=2

# Check database status
echo "🔍 Checking database status..."
python manage.py check_db

echo "✅ Build completed successfully!"
echo "🌐 Service will be available at your Render URL"