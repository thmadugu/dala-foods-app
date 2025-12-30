# Use Python 3.11
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy files
COPY . /app

# Upgrade pip and install dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Expose port
EXPOSE 5000

# Start the app
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
