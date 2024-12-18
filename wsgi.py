import sys
import os

# Add your project directory to Python path
path = '/home/zhimajohn/spss_app'  # Make sure this matches your username
if path not in sys.path:
    sys.path.append(path)

# Create uploads directory if it doesn't exist
uploads_path = os.path.join(path, 'uploads')
if not os.path.exists(uploads_path):
    os.makedirs(uploads_path, mode=0o755)

# Import your Flask app
from app import app as application

# Configure your app
application.secret_key = 'your-secret-key-here'  # Must match the one in app.py

# Use the same USERS dictionary as in app.py
application.config['USERS'] = {
    'admin': 'password123'  # Must match the one in app.py
}

# Configure upload folder
application.config['UPLOAD_FOLDER'] = uploads_path 