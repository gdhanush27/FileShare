# FileShare Pro

A secure, feature-rich file sharing application built with Flask that enables users to upload, manage, and share files with ease.

## Features

### 🔐 User Authentication
- User registration and login system
- Role-based access control (Admin/User)
- Secure password management
- Session-based authentication with server-side storage
- Public user profiles accessible without login

### 📁 File Management
- Upload single or multiple files (up to 5 files at once)
- Support for file bundles with visual distinction (purple theme)
- Download individual files or entire bundles
- Configurable file size limit (default: 40 MB per file)
- All file types supported
- View file details (size, type, upload date)
- Smart storage quota enforcement

### 👥 User Features
- Personal file dashboard
- Public user profiles at `/u/<username>`
- Upload and manage your own files
- Delete individual files or all files at once
- View file metadata (timestamp, size, type)
- **Storage Management:**
  - Personal storage quota with visual progress bar
  - Color-coded storage indicators (green/yellow/red)
  - Configurable storage limits per user
  - Public/private storage visibility toggle
- **Profile Management:**
  - Change password securely
  - View account information
  - Control storage statistics visibility

### 🛡️ Admin Features
- Comprehensive admin dashboard with analytics
- **User Management:**
  - Create new users
  - Delete users and their files
  - Reset user passwords
  - Set individual user storage limits
- View all files across all users
- Storage usage statistics and visualization
- File type distribution charts
- User activity monitoring
- **Configurable Settings:**
  - Maximum file size
  - Maximum files per bundle
  - Registration toggle (open/closed)
  - Total server storage limit (MB)
  - Default user storage limit (MB)
- Real-time storage quota tracking

### 📊 Analytics Dashboard
- Total files and bundles count
- Total users count
- Storage usage visualization with percentage
- File type distribution charts
- User storage usage breakdown
- Upload timeline
- Per-user storage limits display

### 🎨 UI/UX Features
- Modern, responsive design
- Mobile-friendly interface
- Color-coded file bundles (purple) vs regular files (blue)
- Bootstrap-based styling
- Chart.js visualizations
- Progress bars for storage usage
- Flash messages for user feedback

## Installation

### Prerequisites
- Python 3.7 or higher
- pip package manager

### Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd filesharepro
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**
   ```bash
   python app.py
   ```

4. **Access the application**
   - Open your browser and navigate to `http://localhost:5000`
   - Default admin credentials:
     - Username: `gdhanush270`
     - Password: `ttpod123`

## Project Structure

```
filesharepro/
├── app.py                      # Main application file
├── requirements.txt            # Python dependencies
├── README.md                   # Documentation
├── files_db.json              # File metadata storage (auto-generated)
├── users.json                 # User data storage (auto-generated)
├── uploads/                   # Uploaded files directory
├── flask_session/             # Server-side session storage
└── templates/                 # HTML templates
    ├── index.html             # Main file listing page
    ├── login.html             # Login page
    ├── register.html          # Registration page
    ├── profile.html           # User profile page
    ├── file.html              # Single file view
    ├── bundle.html            # Bundle view
    └── admin_dashboard.html   # Admin dashboard
```

## Configuration

### Application Settings
Configure the following in `app.py`:

```python
# Maximum file size
app.config['MAX_CONTENT_LENGTH'] = 40 * 1024 * 1024  # 40 MB

# Upload folder
UPLOAD_FOLDER = 'uploads'

# Session lifetime
app.config['PERMANENT_SESSION_LIFETIME'] = 86400  # 24 hours

# Application settings (configurable via admin dashboard)
SETTINGS = {
    'max_file_size_mb': 40,
    'max_files_per_bundle': 5,
    'registration_open': True,
    'total_server_storage_mb': 102400,  # 100 GB
    'default_user_storage_mb': 1024     # 1 GB per user
}
```

### Admin Users
Modify the `ADMIN_USERS` set in `app.py`:

```python
ADMIN_USERS = {'gdhanush270'}
```

### Storage Limits
- **Server Storage:** Configurable via admin dashboard (default: 100 GB)
- **User Storage:** Configurable per user via admin dashboard (default: 1 GB)
- Users cannot upload files if it would exceed their storage quota
- Storage usage is tracked and displayed with visual progress bars

## Usage

### For Users

1. **Register an account** (if registration is open)
   - Navigate to `/register`
   - Enter username and password
   - Confirm password

2. **Upload files**
   - Click "Choose Files" on the main page
   - Select up to 5 files
   - Click "Upload"
   - Files are checked against your storage quota before upload

3. **Manage files**
   - View all your uploaded files
   - Click on a file to view details
   - Download files individually
   - Delete files when no longer needed

4. **Manage your profile**
   - Access your profile at `/u/<your-username>`
   - Change your password
   - View your storage usage with visual indicators
   - Toggle storage visibility (public/private)
   - View file and bundle counts

5. **View other users**
   - Visit `/u/<username>` to view any user's public profile
   - See their storage stats if they've made them public
   - No login required to view public profiles

### For Admins

1. **Access admin dashboard**
   - Navigate to `/admin`
   - View comprehensive analytics

2. **Manage users**
   - Create new users
   - Reset user passwords
   - Delete users and their files
   - Set individual user storage limits

3. **Configure settings**
   - Adjust maximum file size
   - Set maximum files per bundle
   - Configure total server storage limit
   - Set default user storage limit
   - Enable/disable registration

4. **Monitor storage**
   - View total storage usage
   - Track storage by user
   - See file type distribution
   - Monitor individual user quotas

## Security Features

- Secure filename handling with `werkzeug.utils.secure_filename`
- Server-side session storage
- Password protection (consider implementing hashing for production)
- Role-based access control
- File ownership verification before deletion
- Session-based authentication
- Storage quota enforcement to prevent abuse
- Public/private profile controls

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET, POST | Main file upload and listing page |
| `/login` | GET, POST | User login |
| `/register` | GET, POST | User registration |
| `/logout` | GET | User logout |
| `/u/<username>` | GET, POST | User profile page (public view + password change) |
| `/file/<file_id>` | GET | View file details |
| `/download/<file_id>` | GET | Download file |
| `/delete/<file_id>` | POST | Delete single file |
| `/delete_all` | POST | Delete all user files |
| `/admin` | GET, POST | Admin dashboard and settings |
| `/admin/create_user` | POST | Create new user (admin only) |
| `/admin/reset_password` | POST | Reset user password (admin only) |
| `/admin/delete_user` | POST | Delete user (admin only) |
| `/admin/set_user_storage` | POST | Set user storage limit (admin only) |

## Dependencies

- **Flask 3.0.0** - Web framework
- **Flask-Session 0.5.0** - Server-side session support
- **Werkzeug 3.0.0** - WSGI utility library
- **cachelib 0.10.2** - Caching library for sessions

## Production Deployment

⚠️ **Important**: This application is intended for development. Before deploying to production:

1. **Change the secret key**
   ```python
   app.secret_key = 'your-secure-random-key-here'
   ```

2. **Implement password hashing**
   - Use `werkzeug.security.generate_password_hash` and `check_password_hash`
   - Never store plain text passwords

3. **Configure a production WSGI server**
   - Use Gunicorn, uWSGI, or similar
   - Don't use Flask's built-in development server

4. **Set up HTTPS**
   - Use SSL/TLS certificates
   - Enforce HTTPS for all connections

5. **Configure proper file storage**
   - Use a dedicated storage service for uploaded files
   - Implement proper backup strategies

6. **Set environment variables**
   - Move sensitive configuration to environment variables
   - Use `.env` files with python-dotenv

7. **Disable debug mode**
   ```python
   app.run(debug=False)
   ```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is open source and available under the [GNU GENERAL PUBLIC LICENSE](LICENSE).

## Authors

- gdhanush270

## Support

For issues, questions, or contributions, please open an issue in the repository.

---

## Recent Updates

### Storage Management System
- Per-user storage quotas with configurable limits
- Visual progress bars showing storage usage
- Color-coded indicators (green < 75%, yellow 75-90%, red ≥ 90%)
- Upload restrictions when quota is exceeded
- Admin controls for setting individual user limits

### Profile System
- Public user profiles accessible at `/u/<username>`
- Profile viewable without login
- Password change functionality (own profile only)
- Public/private storage visibility toggle
- Storage statistics display

### UI Enhancements
- Mobile-responsive design
- Bundle files highlighted with purple theme
- Regular files use blue theme
- Improved navigation and user experience
- Bootstrap-powered modern interface
