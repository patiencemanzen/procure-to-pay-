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

# Check environment for debugging
python manage.py collectstatic --noinput
python manage.py migrate

echo "✅ Build completed successfully!"