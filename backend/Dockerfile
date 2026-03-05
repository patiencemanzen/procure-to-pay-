# Use a slim Python image as the base
FROM python:3.11.5-slim-bullseye

# Set environment variables for Python
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Set the working directory inside the container
WORKDIR /code

# Create a non-root user for better security
RUN useradd -m -u 1000 appuser

# Copy requirements file and install dependencies
COPY --chown=appuser:appuser requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire Django project into the container
COPY --chown=appuser:appuser . .

# Remove any cached Python files
RUN find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null; \
    find . -type f -name "*.pyc" -delete

# Switch to non-root user
USER appuser

# Expose the port Django will run on
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000').read()" || exit 1

# Command to run the Django development server
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]