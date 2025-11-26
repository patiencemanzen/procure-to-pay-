#!/bin/bash

# Render build script for Django
# This script runs during the build process on Render

echo "🚀 Starting Render build process..."

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Check environment for debugging
python manage.py collectstatic --noinput
python manage.py migrate

echo "✅ Build completed successfully!"