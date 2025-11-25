# Use a slim Python image as the base
FROM python:3.11.5-slim-bullseye

# Set environment variables for Python
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory inside the container
WORKDIR /code

# Copy requirements file and install dependencies
COPY ./requirements.txt /code/
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire Django project into the container
COPY . /code/

# Remove any cached Python files
RUN find /code -name "*.pyc" -delete
RUN find /code -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

# Expose the port Django will run on
EXPOSE 8000

# Command to run the Django development server
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]