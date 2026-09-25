"""
Saark Web Server - Enterprise Web Application
Main web server file for the online web application
"""

import os
import sys

# Add the web_app directory to Python path
web_app_path = os.path.join(os.path.dirname(__file__), 'web_app')
sys.path.insert(0, web_app_path)

# Change to web_app directory to ensure correct relative paths
os.chdir(web_app_path)

# Import and run the web application
from app import app, init_app

if __name__ == '__main__':
    print("=" * 60)
    print("Starting Saark Web Server")
    print("=" * 60)
    print(f"Web Application Directory: {web_app_path}")
    print(f"Python Version: {sys.version}")
    print()
    
    # Initialize the application (create directories, databases, etc.)
    init_app()
    
    print("Access Information:")
    print("  Local: http://127.0.0.1:5000")
    print("  Network: http://192.168.1.116:5000")
    print()
    print("Login Credentials:")
    print("  Username: a")
    print("  Password: a")
    print()
    print("Press CTRL+C to stop the server")
    print("=" * 60)
    print()
    
    # Run the Flask application
    app.run(host='0.0.0.0', port=5000, debug=False)