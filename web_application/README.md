# CRM & Production Management Web Application

Complete web-based version of the desktop CRM/Production management system with separate data storage.

## 📁 Project Structure

```
web_application/
├── app.py                          # Main Flask application
├── convert_desktop_to_web.py        # Data conversion script
├── requirements.txt                 # Python dependencies
├── templates/                       # HTML templates
│   ├── base.html                  # Base template with navigation
│   ├── dashboard.html             # Dashboard page
│   ├── customers.html              # Customer management page
│   ├── production.html            # Production management page
│   └── login.html                  # Login page
├── static/                          # Static files (CSS, JS, images)
├── config/                          # Configuration files
└── web_data/                        # SEPARATE DATA FOLDER
    ├── databases/                   # Database files
    │   └── main_database.db        # Main SQLite database
    ├── customer_photos/             # Customer photos
    ├── production_docs/             # Production documents
    ├── reports/                     # Generated reports
    ├── exports/                     # Excel/CSV exports
    └── Production/                  # Production batch folders
```

## 🚀 Quick Start

### 1. Install Dependencies
```bash
cd web_application
pip install -r requirements.txt
```

### 2. Convert Desktop Data (Optional)
If you have existing desktop data:
```bash
python convert_desktop_to_web.py
```

### 3. Start the Web Application
```bash
python app.py
```

### 4. Access the Application
- Open browser and go to: `http://127.0.0.1:5000`
- Default login: `admin` / `admin123`

## 🎯 Features

### **Separate Data Storage**
- All data stored in `web_data/` folder
- Database files in `web_data/databases/`
- Customer photos in `web_data/customer_photos/`
- Production documents in `web_data/production_docs/`
- Easy backup and migration

### **Web-Based Access**
- Access from any device with a browser
- No software installation required
- Mobile-friendly responsive design
- Real-time multi-user access

### **Complete Feature Conversion**
- **Customer Management**: Full CRM functionality
- **Production Management**: Batch and testing management
- **Enquiry Management**: Status tracking
- **File Upload/Download**: Photos and documents
- **Data Export**: CSV/Excel exports
- **User Authentication**: Secure login system

### **Desktop to Web Conversion**
- Converts customer CSV data
- Converts production batch data
- Converts testing records
- Copies customer photos
- Copies production documents
- Maintains data integrity

## 📊 Data Flow

```
Desktop Data → convert_desktop_to_web.py → web_data/databases/
                                                   ↓
                                              Flask App
                                                   ↓
                                            Web Interface
```

## 🔧 Configuration

### Database Configuration
Located in `app.py` under `Config` class:
- `WEB_DATA_DIR`: Path to web_data folder
- `DATABASE_DIR`: Path to database files
- Various upload directories

### Security Configuration
- `SECRET_KEY`: Change in production
- User authentication system
- File upload restrictions
- Database access controls

## 🌐 API Endpoints

### Authentication
- `POST /api/login` - User login
- `POST /api/logout` - User logout

### Customer Management
- `GET /api/customers` - Get all customers
- `POST /api/customers` - Add customer
- `PUT /api/customers/<id>` - Update customer
- `DELETE /api/customers/<id>` - Delete customer

### Production Management
- `GET /api/production/batches` - Get all batches
- `POST /api/production/batches` - Add batch
- `PUT /api/production/batches/<id>` - Update batch
- `DELETE /api/production/batches/<id>` - Delete batch

### Enquiry Management
- `GET /api/enquiry_status` - Get enquiry statuses
- `POST /api/enquiry_status` - Update enquiry status

### File Operations
- `POST /api/upload/customer_photo` - Upload customer photo
- `GET /web_data/customer_photos/<company>/<file>` - Serve photos

### Data Management
- `GET /api/export/customers` - Export customer data
- `GET /api/export/production` - Export production data
- `POST /api/data/backup` - Create database backup
- `GET /api/data/stats` - Get data statistics

## 🔄 Data Conversion Process

### Automatic Conversion
The `convert_desktop_to_web.py` script:
1. Reads desktop CSV files
2. Creates web database schema
3. Converts all data formats
4. Copies files and photos
5. Maintains data relationships

### Manual Conversion
If needed, you can manually:
1. Export desktop data to CSV
2. Import into web database
3. Copy files to appropriate folders

## 🛠️ Deployment Options

### Local Development
```bash
python app.py
# Access at http://127.0.0.1:5000
```

### Network Deployment
```bash
python app.py --host=0.0.0.0
# Access at http://your-ip:5000
```

### Production Deployment
- Use Gunicorn + Nginx
- Configure SSL/HTTPS
- Set up domain name
- Configure firewall rules

## 🔒 Security Features

- User authentication with password hashing
- File upload restrictions
- SQL injection protection
- CORS configuration
- Session management
- Input validation

## 📱 Responsive Design

- Bootstrap 5.1 framework
- Mobile-friendly interface
- Responsive tables
- Touch-friendly controls
- Adaptive layouts

## 🎨 UI Features

- Modern Bootstrap interface
- Real-time notifications
- Modal dialogs for forms
- Search and filter functionality
- Status indicators
- Quick action buttons

## 📈 Monitoring

### Database Statistics
- Customer count
- Production batch count
- Testing record count
- Enquiry status count

### Activity Tracking
- Recent customer additions
- Recent production batches
- User activity logs
- Data synchronization logs

## 🔄 MQTT Integration Ready

The web application is designed to integrate with your existing MQTT setup:
- Can add MQTT client for real-time updates
- Synchronization with desktop clients
- Server/client architecture support
- Real-time notifications

## 🚀 Next Steps

1. **Test Local Installation**: Run the web application locally
2. **Convert Desktop Data**: Run the conversion script
3. **Test Functionality**: Verify all features work
4. **Add MQTT Integration**: Integrate with your MQTT broker
5. **Deploy to Server**: Deploy to your web server
6. **Configure Domain**: Set up domain name and SSL
7. **User Training**: Train users on web interface

## 📞 Support

For issues or questions:
1. Check the web application logs
2. Verify database connectivity
3. Test API endpoints
4. Review conversion logs
5. Check file permissions

## 🎯 Benefits of Web Application

1. **Universal Access**: Works on any device
2. **No Installation**: Users don't need to install software
3. **Centralized Data**: All data in `web_data/` folder
4. **Easy Updates**: Update once, all users get it
5. **Better Collaboration**: Multiple users can work simultaneously
6. **Mobile Access**: Works on smartphones and tablets
7. **Better Security**: Centralized security management
8. **Easy Backup**: Single folder to backup

Your complete CRM/Production management system is now available as a web application with separate data storage!