# GitHub Deployment Guide for Enterprise Web Application

## 🚀 Deploy Your Web Application Online

### Step 1: Prepare Your Project for GitHub

#### 1.1 Create a .gitignore file
Create `.gitignore` in your web_application folder to exclude unnecessary files:

```
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
venv/
env/
ENV/
.venv

# Database
web_data/databases/*.db
web_data/databases/*.db-journal
web_data/customer_photos/*
web_data/production_docs/*
web_data/exports/*
web_data/reports/*
web_data/Production/*
web_data/warehouse/*
web_data/finance/*
web_data/hr/*
web_data/projects/*
web_data/rnd/*
web_data/legal/*
web_data/qc/*
web_data/it/*
web_data/supply_chain/*

# Logs
*.log

# OS
.DS_Store
Thumbs.db

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# Environment variables
.env
.env.local
```

#### 1.2 Create requirements.txt (already exists)
```
Flask==3.1.3
Werkzeug==3.1.8
paho-mqtt==1.6.1
openpyxl==3.1.2
gunicorn==21.2.0
psycopg2-binary==2.9.9
```

### Step 2: Create GitHub Repository

#### 2.1 Initialize Git in Your Project
```bash
cd "D:\python code\porduct selector\web_application"
git init
```

#### 2.2 Add All Files
```bash
git add .
```

#### 2.3 Create Initial Commit
```bash
git commit -m "Initial commit - Enterprise Web Application"
```

#### 2.4 Create GitHub Repository
1. Go to https://github.com
2. Click "+" → "New repository"
3. Name it: `enterprise-web-application`
4. Make it Public or Private
5. Click "Create repository"

#### 2.5 Connect Local Repository to GitHub
```bash
git remote add origin https://github.com/YOUR_USERNAME/enterprise-web-application.git
git branch -M main
git push -u origin main
```

### Step 3: Deploy to Web Hosting Service

#### Option A: PythonAnywhere (Recommended for Flask)
**Free tier available!**

1. **Sign Up**
   - Go to https://www.pythonanywhere.com
   - Create a free account

2. **Create Web App**
   - Dashboard → "Web" → "Add a new web app"
   - Choose "Flask"
   - Select Python version (3.10+)

3. **Upload Your Code**
   - Dashboard → "Files" → Upload your project files
   - Upload: app.py, requirements.txt, templates/, static/

4. **Install Dependencies**
   - In PythonAnywhere console:
   ```bash
   pip install -r requirements.txt
   ```

5. **Configure WSGI**
   - Create `wsgi.py` file:
   ```python
   from app import app
   
   if __name__ == "__main__":
       app.run()
   ```

6. **Start Your App**
   - PythonAnywhere will give you a URL like: `yourname.pythonanywhere.com`

#### Option B: Heroku (Popular, requires credit card)
**Free tier available!**

1. **Install Heroku CLI**
   ```bash
   npm install -g heroku
   ```

2. **Login to Heroku**
   ```bash
   heroku login
   ```

3. **Create Heroku App**
   ```bash
   heroku create enterprise-web-app
   ```

4. **Create Procfile**
   Create `Procfile` in your project root:
   ```
   web: gunicorn app:app
   ```

5. **Deploy**
   ```bash
   git push heroku main
   ```

6. **Open Your App**
   ```bash
   heroku open
   ```

#### Option C: Render (Modern, has free tier)
**Free tier available!**

1. **Sign Up**
   - Go to https://render.com
   - Create a free account

2. **Create Web Service**
   - Dashboard → "New +" → "Web Service"
   - Connect your GitHub repository
   - Select "Python" as runtime

3. **Configure Build**
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app`

4. **Deploy**
   - Render will auto-deploy from GitHub

#### Option D: AWS EC2 (Enterprise, paid)
**Professional option**

1. **Launch EC2 Instance**
   - AWS Console → EC2 → Launch Instance
   - Choose Ubuntu server
   - Configure security groups (allow port 5000)

2. **Connect to Server**
   ```bash
   ssh -i your-key.pem ubuntu@your-server-ip
   ```

3. **Install Dependencies**
   ```bash
   sudo apt update
   sudo apt install python3-pip
   sudo pip3 install flask gunicorn
   ```

4. **Upload Your Code**
   - Use `git clone` or `scp` to upload your project

5. **Run Your App**
   ```bash
   gunicorn -b 0.0.0.0:5000 app:app
   ```

### Step 4: Update for Production Deployment

#### 4.1 Create production-ready app.py
Update `app.py` for production:

```python
# Remove debug mode for production
if __name__ == '__main__':
    # Use production WSGI server
    app.run(host='0.0.0.0', port=5000, debug=False)
```

#### 4.2 Update Database Configuration
For production, use PostgreSQL instead of SQLite:

```python
# Update app.py database configuration
import os

if os.environ.get('DATABASE_URL'):
    # Use PostgreSQL in production
    DATABASE_URL = os.environ.get('DATABASE_URL')
else:
    # Use SQLite in development
    DATABASE_DIR = os.path.join(BASE_DIR, 'web_data')
    DATABASE_PATH = os.path.join(DATABASE_DIR, 'databases', 'enterprise_database.db')
```

#### 4.3 Add Environment Variables
Create `.env` file (don't commit to GitHub):
```
SECRET_KEY=your-production-secret-key
DATABASE_URL=postgresql://user:password@host:5432/dbname
FLASK_ENV=production
```

### Step 5: Configure Domain Name (Optional)

#### 5.1 Buy a Domain
- Go to GoDaddy, Namecheap, or Google Domains
- Purchase your domain (e.g., `yourcompany.com`)

#### 5.2 Configure DNS
- Point domain to your hosting service IP address
- Update DNS records (A record, CNAME)

#### 5.3 Configure SSL/HTTPS
- Use Let's Encrypt (free SSL)
- Most hosting services provide free SSL

### Step 6: Set Up Automatic Backups

#### 6.1 Database Backups
- Set up automated database backups
- Schedule daily/weekly backups
- Store backups in cloud storage (AWS S3, Google Drive)

#### 6.2 Code Backups
- GitHub provides version control
- Automatic backups with each commit
- Rollback capability

### Step 7: Security Configuration

#### 7.1 Update Admin Password
```python
# In app.py, change default password
password_hash = generate_password_hash('your-secure-password')
```

#### 7.2 Configure Firewall
- Only allow necessary ports (80, 443, 22)
- Block unauthorized access
- Use security groups (AWS)

#### 7.3 Enable HTTPS
- Force HTTPS for all connections
- Update SSL certificates regularly
- Use secure cookies

### Step 8: Monitor Your Application

#### 8.1 Set Up Monitoring
- Use hosting service monitoring tools
- Set up uptime monitoring (UptimeRobot, Pingdom)
- Configure error tracking (Sentry, Rollbar)

#### 8.2 Logging
- Configure application logging
- Set up log rotation
- Monitor error logs regularly

### Step 9: MQTT Configuration for Online Access

#### 9.1 Update MQTT Configuration
Update `mqtt_config.py` for production:

```python
MQTT_BROKER = os.environ.get('MQTT_BROKER', 'network.saark.in')
MQTT_PORT = int(os.environ.get('MQTT_PORT', 1884))
MQTT_USERNAME = os.environ.get('MQTT_USERNAME')
MQTT_PASSWORD = os.environ.get('MQTT_PASSWORD')
```

#### 9.2 Configure MQTT Broker
- Ensure your MQTT broker allows external connections
- Configure firewall to allow MQTT traffic
- Use TLS for secure MQTT connections

### Step 10: Multi-User Access Setup

#### 10.1 Create User Accounts
- Create separate user accounts for each team member
- Set appropriate permissions and roles
- Configure 2FA for sensitive operations

#### 10.2 Access Control
- Use role-based access control
- Limit admin access to authorized personnel
- Regularly review user permissions

## 🎯 Quick Deployment Steps Summary

### **Easiest Free Option: PythonAnywhere**
1. Sign up at pythonanywhere.com
2. Create Flask web app
3. Upload your files
4. Install requirements
5. Your app is online!

### **Modern Free Option: Render**
1. Sign up at render.com
2. Connect GitHub repository
3. Configure build settings
4. Auto-deploy from GitHub

### **Professional Option: AWS/Heroku**
1. Create account
2. Configure resources
3. Deploy from GitHub
4. Configure domain and SSL

## 🔧 Important Files to Create

### **wsgi.py** (Required for production deployment)
```python
from app import app

if __name__ == "__main__":
    app.run()
```

### **Procfile** (Required for Heroku)
```
web: gunicorn app:app
```

### **runtime.txt** (Python version specification)
```
python-3.10.12
```

### **.env** (Environment variables - don't commit to GitHub)
```
SECRET_KEY=your-secret-key
FLASK_ENV=production
DATABASE_URL=your-database-url
```

## 🌐 Your Online Access URLs

After deployment, you'll have URLs like:
- **PythonAnywhere**: `yourname.pythonanywhere.com`
- **Render**: `your-app.onrender.com`
- **Heroku**: `your-app.herokuapp.com`
- **Custom Domain**: `yourcompany.com`

## 🔒 Security Best Practices

1. **Never commit secrets** to GitHub
2. **Use environment variables** for sensitive data
3. **Enable HTTPS** for all connections
4. **Regular updates** of dependencies
5. **Strong passwords** for all accounts
6. **Regular backups** of database and code
7. **Monitor access logs** regularly
8. **Use 2FA** for admin accounts

## 📱 Mobile Access

Once deployed online:
- Access from any device with a browser
- Works on smartphones, tablets, laptops
- No software installation needed
- Real-time multi-user access

## 🎉 Benefits of Online Deployment

- **24/7 Access** from anywhere
- **Multi-user collaboration**
- **Automatic backups** with version control
- **Easy updates** via Git push
- **Professional appearance** with custom domain
- **Scalable** to handle more users
- **Secure** with SSL/HTTPS

Your enterprise web application can now be controlled online from anywhere in the world!