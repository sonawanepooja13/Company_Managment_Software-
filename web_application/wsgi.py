"""
WSGI entry point for production deployment
Required for hosting services like PythonAnywhere, Heroku, etc.
"""

from app import app

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=False)