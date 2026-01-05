from flask import Flask, render_template, request, redirect, url_for, send_from_directory, flash, session, send_file
from flask_session import Session
from werkzeug.utils import secure_filename
import os
import uuid
from datetime import datetime, timedelta
import mimetypes
import json
from PIL import Image
import io

app = Flask(__name__)
app.secret_key = "super-secret"
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
SESSION_FOLDER = os.path.join(os.path.dirname(__file__), 'flask_session')
PROFILE_PICTURES_FOLDER = os.path.join(os.path.dirname(__file__), 'profile_pictures')

# Configure server-side session storage
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = SESSION_FOLDER
app.config['SESSION_PERMANENT'] = True
app.config['SESSION_USE_SIGNER'] = True
app.config['SESSION_FILE_THRESHOLD'] = 100
app.config['PERMANENT_SESSION_LIFETIME'] = 86400  # 24 hours in seconds

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 40 * 1024 * 1024  # 40 MB
ALLOWED_EXTENSIONS = None  # None means allow all file types

# Initialize server-side sessions
Session(app)

# File path for user storage
USERS_FILE = os.path.join(os.path.dirname(__file__), 'users.json')

# File path for file database storage
FILES_DB_FILE = os.path.join(os.path.dirname(__file__), 'files_db.json')

# File path for settings storage
SETTINGS_FILE = os.path.join(os.path.dirname(__file__), 'settings.json')

# File path for recovery requests storage
RECOVERY_REQUESTS_FILE = os.path.join(os.path.dirname(__file__), 'recovery_requests.json')

# In-memory file info storage: {file_id: {filename, path, timestamp}}
file_db = {}

# Helper to check admin
ADMIN_USERS = {'gdhanush270'}

# Application settings
SETTINGS = {
    'app_name': 'FileShare Pro',
    'max_file_size_mb': 40,
    'max_files_per_bundle': 5,
    'registration_open': True,
    'total_server_storage_mb': 500,  # Total server storage in MB (100 GB)
    'user_storage_limit_mb': 50  # User storage limit in MB (applies to all users)
}

def load_settings():
    """Load settings from JSON file"""
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, 'r') as f:
                loaded_settings = json.load(f)
                # Merge with default settings to ensure all keys exist
                for key, value in loaded_settings.items():
                    SETTINGS[key] = value
        except (json.JSONDecodeError, IOError):
            pass

def save_settings():
    """Save settings to JSON file"""
    try:
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(SETTINGS, f, indent=2)
    except IOError:
        pass

def load_users():
    """Load users from JSON file"""
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    # Return default admin users if file doesn't exist or is corrupted
    return {
        'gdhanush270': {'password': 'ttpod123', 'role': 'admin'},
    }

def save_users(users):
    """Save users to JSON file"""
    try:
        with open(USERS_FILE, 'w') as f:
            json.dump(users, f, indent=2)
    except IOError:
        pass

def load_files_db():
    """Load files database from JSON file"""
    if os.path.exists(FILES_DB_FILE):
        try:
            with open(FILES_DB_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {}

def save_files_db(files_db):
    """Save files database to JSON file"""
    try:
        with open(FILES_DB_FILE, 'w') as f:
            json.dump(files_db, f, indent=2)
    except IOError:
        pass

def load_recovery_requests():
    """Load recovery requests from JSON file"""
    if os.path.exists(RECOVERY_REQUESTS_FILE):
        try:
            with open(RECOVERY_REQUESTS_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {}

def save_recovery_requests(requests):
    """Save recovery requests to JSON file"""
    try:
        with open(RECOVERY_REQUESTS_FILE, 'w') as f:
            json.dump(requests, f, indent=2)
    except IOError:
        pass

# Load settings on startup
load_settings()

# Load users on startup
USERS = load_users()

# Load files database on startup
file_db = load_files_db()

# Load recovery requests on startup
recovery_requests = load_recovery_requests()

# Application name (pulled from settings)
APP_NAME = SETTINGS.get('app_name', 'FileShare Pro')

def is_admin(username):
    return username.lower() in ADMIN_USERS

def allowed_file(filename):
    if ALLOWED_EXTENSIONS is None:
        return True
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/register', methods=['GET', 'POST'])
def register():
    print("=== REGISTER ROUTE CALLED ===")
    print(f"Request method: {request.method}")
    if not SETTINGS.get('registration_open', True):
        flash('Registration is currently disabled. Please contact an admin.', 'error')
        return redirect(url_for('login'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        print(f"Registration attempt - Username: {username}, Password: {password}, Confirm: {confirm_password}")
        if not username or not password or not confirm_password:
            flash('All fields are required!', 'error')
            return render_template('register.html')
        if password != confirm_password:
            flash('Passwords do not match!', 'error')
            return render_template('register.html')
        
        # Convert username to lowercase for case-insensitive comparison
        username_lower = username.lower()
        if username_lower in USERS:
            # Check if user was deleted and 30 days have passed
            existing_user = USERS[username_lower]
            if existing_user.get('deleted_at'):
                deleted_at = datetime.fromisoformat(existing_user['deleted_at'])
                deletion_date = deleted_at + timedelta(days=30)
                
                # If 30 days have passed, delete old account and create new one
                if datetime.now() > deletion_date:
                    # Delete old user's profile picture if exists
                    if existing_user.get('profile_picture'):
                        old_pic_path = os.path.join(PROFILE_PICTURES_FOLDER, existing_user['profile_picture'])
                        if os.path.exists(old_pic_path):
                            try:
                                os.remove(old_pic_path)
                            except:
                                pass
                    
                    # Delete old user's files
                    ids_to_delete = []
                    for fid, info in list(file_db.items()):
                        if info.get('owner') == username_lower:
                            ids_to_delete.append(fid)
                    
                    for fid in ids_to_delete:
                        info = file_db.get(fid)
                        if info:
                            if info.get('is_bundle'):
                                for child_id in info.get('files', []):
                                    child_info = file_db.get(child_id)
                                    if child_info and os.path.exists(child_info['path']):
                                        try:
                                            os.remove(child_info['path'])
                                        except:
                                            pass
                                    file_db.pop(child_id, None)
                                file_db.pop(fid, None)
                            else:
                                if os.path.exists(info['path']):
                                    try:
                                        os.remove(info['path'])
                                    except:
                                        pass
                                file_db.pop(fid, None)
                    
                    save_files_db(file_db)
                    # Now create new user (continue below)
                else:
                    flash('Username already exists!', 'error')
                    return render_template('register.html')
            else:
                flash('Username already exists!', 'error')
                return render_template('register.html')
        
        USERS[username_lower] = {'password': password, 'role': 'user', 'storage_limit_mb': 50}
        save_users(USERS)
        
        # Remove any pending recovery request for this username
        if username_lower in recovery_requests:
            recovery_requests.pop(username_lower, None)
            save_recovery_requests(recovery_requests)
        
        print(f"User registered successfully: {username_lower}")
        print(f"Current users: {list(USERS.keys())}")
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    print("Returning register.html template")
    return render_template('register.html', APP_NAME=APP_NAME)

@app.route('/recover', methods=['GET', 'POST'])
def recover():
    """Recovery page for permanently deleted accounts (>30 days)"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            flash('Username and password are required!', 'error')
            return render_template('recover.html', APP_NAME=APP_NAME)
        
        # Convert username to lowercase
        username_lower = username.lower()
        user = USERS.get(username_lower)
        
        # Always show the same message for security (prevent username enumeration)
        # Only process if credentials are correct
        should_process = False
        
        if user and user['password'] == password and user.get('deleted_at'):
            deleted_at = datetime.fromisoformat(user['deleted_at'])
            deletion_date = deleted_at + timedelta(days=30)
            
            # Only process if 30 days have passed and no existing request
            if datetime.now() > deletion_date and username_lower not in recovery_requests:
                should_process = True
        
        # Process the recovery request if credentials are correct
        if should_process:
            recovery_requests[username_lower] = {
                'username': username_lower,
                'requested_at': datetime.now().isoformat(),
                'deleted_at': user['deleted_at'],
                'role': user.get('role', 'user')
            }
            save_recovery_requests(recovery_requests)
        
        # Always show the same message regardless of success
        flash('Request will be sent if the credentials are correct.', 'info')
        return redirect(url_for('login'))
    
    return render_template('recover.html', APP_NAME=APP_NAME)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username') or ""
        password = request.form.get('password') or ""
        print(f"Login attempt - Username: {username}, Password: {password}")
        
        # Convert username to lowercase for case-insensitive lookup
        username_lower = username.lower()
        user = USERS.get(username_lower)
        print(f"User found: {user}")
        if user and user['password'] == password:
            # Check if account is marked for deletion
            if user.get('deleted_at'):
                deleted_at = datetime.fromisoformat(user['deleted_at'])
                deletion_date = deleted_at + timedelta(days=30)
                
                # Check if 30 days have passed
                if datetime.now() > deletion_date:
                    flash('Your account has been permanently deleted. Visit the recovery page to restore your account.', 'error')
                    return render_template('login.html', APP_NAME=APP_NAME)
                else:
                    # Account is scheduled for deletion, allow login to recover
                    session['username'] = username_lower
                    session['role'] = user['role']
                    flash(f'Your account is scheduled for deletion on {deletion_date.strftime("%B %d, %Y")}. Visit your profile to recover it.', 'error')
                    return redirect(url_for('index'))
            
            session['username'] = username_lower
            session['role'] = user['role']
            print(f"Login successful for: {username_lower}")
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            print(f"Login failed for: {username_lower}")
            flash('Invalid username or password!', 'error')
            return render_template('login.html', APP_NAME=APP_NAME)
    return render_template('login.html', APP_NAME=APP_NAME)

@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('role', None)
    flash('Logged out successfully!', 'success')
    return redirect(url_for('login'))

@app.route('/u/<username>', methods=['GET', 'POST'])
def profile(username):
    # Check if the profile user exists
    if username not in USERS:
        flash('User not found!', 'error')
        return redirect(url_for('login'))
    
    # Determine if viewing own profile
    current_user = session.get('username')
    is_own_profile = (current_user == username)
    
    if request.method == 'POST':
        # Password change requires login
        if 'username' not in session:
            flash('Please login to change your password!', 'error')
            return redirect(url_for('login'))
        
        # Only allow password change for own profile
        if not is_own_profile:
            flash('You can only change your own password!', 'error')
            return redirect(url_for('profile', username=username))
        
        # Handle storage visibility toggle
        if 'toggle_storage_visibility' in request.form:
            user = USERS.get(username)
            current_visibility = user.get('storage_public', True)
            user['storage_public'] = not current_visibility
            save_users(USERS)
            flash(f"Storage visibility set to {'public' if user['storage_public'] else 'private'}!", 'success')
            return redirect(url_for('profile', username=username))
        
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        # Validate inputs
        if not current_password or not new_password or not confirm_password:
            flash('All fields are required!', 'error')
            return render_template('profile.html', username=username, user_info=USERS.get(username, {}), is_own_profile=is_own_profile, APP_NAME=APP_NAME)
        
        # Check current password
        user = USERS.get(username)
        if not user or user['password'] != current_password:
            flash('Current password is incorrect!', 'error')
            return render_template('profile.html', username=username, user_info=USERS.get(username, {}), is_own_profile=is_own_profile, APP_NAME=APP_NAME)
        
        # Check new passwords match
        if new_password != confirm_password:
            flash('New passwords do not match!', 'error')
            return render_template('profile.html', username=username, user_info=USERS.get(username, {}), is_own_profile=is_own_profile, APP_NAME=APP_NAME)
        
        # Update password
        USERS[username]['password'] = new_password
        save_users(USERS)
        flash('Password changed successfully!', 'success')
        return redirect(url_for('profile', username=username))
    
    user_info = USERS.get(username, {})
    
    # Initialize storage_public if not set
    if 'storage_public' not in user_info:
        user_info['storage_public'] = True
        USERS[username] = user_info
        save_users(USERS)
    
    # Determine if storage should be visible
    # Admins can always see storage, even if private
    is_admin_viewing = current_user and is_admin(current_user)
    storage_visible = is_own_profile or user_info.get('storage_public', True) or is_admin_viewing
    
    # Calculate user's storage usage
    total_storage_bytes = 0
    file_count = 0
    bundle_count = 0
    
    for file_id, file_info in file_db.items():
        if file_info.get('owner') == username:
            if file_info.get('is_bundle'):
                bundle_count += 1
            else:
                file_count += 1
                if os.path.exists(file_info['path']):
                    total_storage_bytes += os.path.getsize(file_info['path'])
    
    # Format storage size
    def format_bytes(bytes_val):
        if bytes_val < 1024:
            return f"{bytes_val} B"
        elif bytes_val < 1024 * 1024:
            return f"{bytes_val/1024:.2f} KB"
        elif bytes_val < 1024 * 1024 * 1024:
            return f"{bytes_val/1024/1024:.2f} MB"
        else:
            return f"{bytes_val/1024/1024/1024:.2f} GB"
    
    # Calculate storage percentage (use user-specific limit or default to 50MB)
    user_limit_mb = user_info.get('storage_limit_mb', 50)
    user_limit_bytes = user_limit_mb * 1024 * 1024
    storage_percentage = (total_storage_bytes / user_limit_bytes * 100) if user_limit_bytes > 0 else 0
    
    storage_info = {
        'total_storage': format_bytes(total_storage_bytes),
        'total_storage_bytes': total_storage_bytes,
        'file_count': file_count,
        'bundle_count': bundle_count,
        'storage_limit': format_bytes(user_limit_bytes),
        'storage_limit_bytes': user_limit_bytes,
        'storage_percentage': round(storage_percentage, 1)
    }
    
    # Add deletion info if account is marked for deletion
    if user_info.get('deleted_at'):
        deleted_at = datetime.fromisoformat(user_info['deleted_at'])
        deletion_date = deleted_at + timedelta(days=30)
        user_info['deletion_date'] = deletion_date.strftime('%B %d, %Y')
    
    return render_template('profile.html', user_info=user_info, username=username, storage_info=storage_info, is_own_profile=is_own_profile, storage_visible=storage_visible, APP_NAME=APP_NAME, is_admin=is_admin(session.get('username', '')))

@app.route('/u/<username>/upload_profile_picture', methods=['POST'])
def upload_profile_picture(username):
    # Check if user is logged in and viewing own profile
    if 'username' not in session:
        flash('Please login to upload a profile picture!', 'error')
        return redirect(url_for('login'))
    
    if session['username'] != username:
        flash('You can only change your own profile picture!', 'error')
        return redirect(url_for('profile', username=username))
    
    if 'profile_picture' not in request.files:
        flash('No file selected!', 'error')
        return redirect(url_for('profile', username=username))
    
    file = request.files['profile_picture']
    
    if file.filename == '':
        flash('No file selected!', 'error')
        return redirect(url_for('profile', username=username))
    
    # Check if file is an image
    mime_type, _ = mimetypes.guess_type(file.filename)
    if not mime_type or not mime_type.startswith('image/'):
        flash('Only image files are allowed for profile pictures!', 'error')
        return redirect(url_for('profile', username=username))
    
    # Save the profile picture
    try:
        # Remove old profile picture if exists
        user = USERS.get(username)
        if user and user.get('profile_picture'):
            old_pic_path = os.path.join(PROFILE_PICTURES_FOLDER, user['profile_picture'])
            if os.path.exists(old_pic_path):
                try:
                    os.remove(old_pic_path)
                except:
                    pass
        
        # Generate unique filename
        file_ext = os.path.splitext(file.filename)[1]
        unique_filename = f"{username}_{uuid.uuid4().hex}{file_ext}"
        file_path = os.path.join(PROFILE_PICTURES_FOLDER, unique_filename)
        
        # Save and resize the image
        img = Image.open(file.stream)
        # Convert RGBA to RGB if necessary
        if img.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
            img = background
        
        # Resize to 300x300 (profile picture standard size)
        img.thumbnail((300, 300), Image.Resampling.LANCZOS)
        img.save(file_path, 'JPEG', quality=85, optimize=True)
        
        # Update user record
        USERS[username]['profile_picture'] = unique_filename
        save_users(USERS)
        
        flash('Profile picture updated successfully!', 'success')
    except Exception as e:
        flash(f'Error uploading profile picture: {str(e)}', 'error')
    
    return redirect(url_for('profile', username=username))

@app.route('/u/<username>/delete_profile_picture', methods=['POST'])
def delete_profile_picture(username):
    """Delete user's profile picture"""
    # Check if user is logged in and viewing own profile
    if 'username' not in session:
        flash('Please login to delete your profile picture!', 'error')
        return redirect(url_for('login'))
    
    if session['username'] != username:
        flash('You can only delete your own profile picture!', 'error')
        return redirect(url_for('profile', username=username))
    
    user = USERS.get(username)
    if user and user.get('profile_picture'):
        # Delete the file
        pic_path = os.path.join(PROFILE_PICTURES_FOLDER, user['profile_picture'])
        if os.path.exists(pic_path):
            try:
                os.remove(pic_path)
            except Exception as e:
                flash(f'Error deleting profile picture file: {str(e)}', 'error')
                return redirect(url_for('profile', username=username))
        
        # Remove from user record
        user['profile_picture'] = None
        save_users(USERS)
        flash('Profile picture deleted successfully!', 'success')
    else:
        flash('No profile picture to delete!', 'error')
    
    return redirect(url_for('profile', username=username))

@app.route('/u/<username>/request_deletion', methods=['POST'])
def request_account_deletion(username):
    """Mark account for deletion with 30-day grace period"""
    if 'username' not in session:
        flash('Please login to delete your account!', 'error')
        return redirect(url_for('login'))
    
    if session['username'] != username:
        flash('You can only delete your own account!', 'error')
        return redirect(url_for('profile', username=username))
    
    # Check if user is admin - prevent admin from self-deletion
    if is_admin(username):
        flash('Admin accounts cannot be deleted. Please contact another administrator.', 'error')
        return redirect(url_for('profile', username=username))
    
    user = USERS.get(username)
    if user:
        # Mark account for deletion
        user['deleted_at'] = datetime.now().isoformat()
        save_users(USERS)
        
        # Log out the user
        session.pop('username', None)
        session.pop('role', None)
        
        deletion_date = (datetime.now() + timedelta(days=30)).strftime('%B %d, %Y')
        flash(f'Your account has been scheduled for deletion on {deletion_date}. You can recover it anytime before then by logging in.', 'success')
        return redirect(url_for('login'))
    
    flash('Account not found!', 'error')
    return redirect(url_for('login'))

@app.route('/u/<username>/recover', methods=['POST'])
def recover_account(username):
    """Recover account from deletion"""
    if 'username' not in session:
        flash('Please login to recover your account!', 'error')
        return redirect(url_for('login'))
    
    if session['username'] != username:
        flash('You can only recover your own account!', 'error')
        return redirect(url_for('profile', username=username))
    
    user = USERS.get(username)
    if user and user.get('deleted_at'):
        # Check if 30 days have passed
        deleted_at = datetime.fromisoformat(user['deleted_at'])
        deletion_date = deleted_at + timedelta(days=30)
        
        if datetime.now() > deletion_date:
            flash('The recovery period has expired. Your account cannot be recovered.', 'error')
            session.pop('username', None)
            session.pop('role', None)
            return redirect(url_for('login'))
        
        # Recover account
        user['deleted_at'] = None
        save_users(USERS)
        flash('Your account has been successfully recovered!', 'success')
    else:
        flash('Account not found or not scheduled for deletion!', 'error')
    
    return redirect(url_for('profile', username=username))

@app.route('/profile_picture/<username>')
def get_profile_picture(username):
    """Serve profile picture for a user"""
    user = USERS.get(username)
    if user and user.get('profile_picture'):
        pic_path = os.path.join(PROFILE_PICTURES_FOLDER, user['profile_picture'])
        if os.path.exists(pic_path):
            return send_from_directory(PROFILE_PICTURES_FOLDER, user['profile_picture'])
    
    # Return default avatar (we'll use a placeholder)
    return '', 404

@app.route('/preview/<file_id>')
def preview_image(file_id):
    """Generate and serve a low-resolution preview for images over 300KB"""
    file_info = file_db.get(file_id)
    if not file_info:
        return 'File not found', 404
    
    file_path = file_info.get('path')
    if not file_path or not os.path.exists(file_path):
        return 'File not found', 404
    
    # Check if it's an image
    mime_type, _ = mimetypes.guess_type(file_info.get('filename', ''))
    if not mime_type or not mime_type.startswith('image/'):
        return 'Not an image', 400
    
    # Check file size
    file_size = os.path.getsize(file_path)
    size_kb = file_size / 1024
    
    # If file is less than 300KB, serve original
    if size_kb < 300:
        return send_file(file_path, mimetype=mime_type)
    
    # Generate low-res preview
    try:
        img = Image.open(file_path)
        
        # Create a thumbnail (max 800x800 for preview)
        img.thumbnail((800, 800), Image.Resampling.LANCZOS)
        
        # Save to BytesIO object
        img_io = io.BytesIO()
        
        # Determine format
        img_format = 'JPEG'
        if mime_type == 'image/png':
            img_format = 'PNG'
        elif mime_type == 'image/gif':
            img_format = 'GIF'
        
        # Convert RGBA to RGB for JPEG
        if img_format == 'JPEG' and img.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
            img = background
        
        img.save(img_io, img_format, quality=70, optimize=True)
        img_io.seek(0)
        
        return send_file(img_io, mimetype=mime_type)
    except Exception as e:
        # If preview generation fails, serve original
        return send_file(file_path, mimetype=mime_type)

@app.route('/', methods=['GET', 'POST'])
def index():
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    role = session.get('role', 'user')
    # Admin toggle: show all files or only own
    show_all = request.args.get('show_all') == '1' if role == 'admin' else False
    if request.method == 'POST':
        if 'files' not in request.files:
            flash('No file part')
            return redirect(request.url)
        files = request.files.getlist('files')
        if not files or all(file.filename == '' for file in files):
            flash('No selected files')
            return redirect(request.url)
        if len(files) > 5:
            flash('Maximum 5 files allowed')
            return redirect(request.url)

        # Calculate current user storage usage
        current_storage_bytes = 0
        for file_id, file_info in file_db.items():
            if file_info.get('owner') == username and not file_info.get('is_bundle'):
                if os.path.exists(file_info['path']):
                    current_storage_bytes += os.path.getsize(file_info['path'])
        
        # Get user storage limit (use user-specific limit or default to 50MB)
        user_data = USERS.get(username, {})
        user_limit_mb = user_data.get('storage_limit_mb', 50)
        user_limit_bytes = user_limit_mb * 1024 * 1024
        
        # Calculate size of files to be uploaded
        upload_size_bytes = 0
        temp_files = []
        for file in files:
            if file:
                # Seek to end to get file size
                file.seek(0, os.SEEK_END)
                file_size = file.tell()
                file.seek(0)  # Reset to beginning
                upload_size_bytes += file_size
                temp_files.append((file, file_size))
        
        # Check if upload would exceed storage limit
        if current_storage_bytes + upload_size_bytes > user_limit_bytes:
            def format_bytes(bytes_val):
                if bytes_val < 1024:
                    return f"{bytes_val} B"
                elif bytes_val < 1024 * 1024:
                    return f"{bytes_val/1024:.2f} KB"
                elif bytes_val < 1024 * 1024 * 1024:
                    return f"{bytes_val/1024/1024:.2f} MB"
                else:
                    return f"{bytes_val/1024/1024/1024:.2f} GB"
            
            available_space = user_limit_bytes - current_storage_bytes
            flash(f'Upload failed! Storage limit exceeded. You have {format_bytes(available_space)} available out of {format_bytes(user_limit_bytes)} total storage.', 'error')
            return redirect(request.url)

        # Create a bundle for multiple files
        bundle_id = str(uuid.uuid4())
        bundle_files = []

        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename or "")
                unique_id = str(uuid.uuid4())
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                unique_filename = f"{unique_id}_{filename}"
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                file.save(file_path)
                file_db[unique_id] = {
                    'filename': filename,
                    'unique_filename': unique_filename,
                    'path': file_path,
                    'timestamp': timestamp,
                    'owner': username,
                    'bundle_id': bundle_id
                }
                bundle_files.append(unique_id)
            else:
                flash(f'Invalid file type: {file.filename}')
                return redirect(request.url)

        # Store bundle info
        if len(bundle_files) > 1:
            file_db[bundle_id] = {
                'filename': f'Bundle of {len(bundle_files)} files',
                'files': bundle_files,
                'timestamp': timestamp,
                'owner': username,
                'is_bundle': True
            }

        # Save files database to file
        save_files_db(file_db)

        flash(f'Successfully uploaded {len(bundle_files)} file(s)!')
        return redirect(url_for('index', show_all='1' if show_all else '0'))

    if role == 'admin' and show_all:
        user_files = file_db
    else:
        user_files = {fid: info for fid, info in file_db.items() if info.get('owner') == username}
    return render_template('index.html', files=user_files, is_admin=(role=='admin'), show_all=show_all, APP_NAME=APP_NAME)

@app.route('/file/<file_id>', methods=['GET'])
def file_page(file_id):
    file_info = file_db.get(file_id)
    if file_info and file_info.get('is_bundle'):
        # This is a bundle, show bundle page
        bundle_files = {fid: file_db.get(fid) for fid in file_info.get('files', [])}
        # Calculate individual file sizes and total bundle size
        total_size_bytes = 0
        for fid, f in bundle_files.items():
            if f and os.path.exists(f['path']):
                size_bytes = os.path.getsize(f['path'])
                f['size'] = (
                    f"{size_bytes} B" if size_bytes < 1024 else
                    f"{size_bytes/1024:.1f} KB" if size_bytes < 1024*1024 else
                    f"{size_bytes/1024/1024:.1f} MB"
                )
                f['size_bytes'] = size_bytes
                total_size_bytes += size_bytes
            else:
                bundle_files[fid] = {'size': 'N/A', 'size_bytes': 0, 'filename': f['filename'] if f else 'Unknown'}
        bundle_size = (
            f"{total_size_bytes} B" if total_size_bytes < 1024 else
            f"{total_size_bytes/1024:.1f} KB" if total_size_bytes < 1024*1024 else
            f"{total_size_bytes/1024/1024:.1f} MB"
        )
        return render_template('bundle.html', bundle_info=file_info, files=bundle_files, file_id=file_id, bundle_size=bundle_size, APP_NAME=APP_NAME)

    file_size = None
    file_type = None
    is_image = False
    size_bytes = 0
    if file_info and os.path.exists(file_info['path']):
        size_bytes = os.path.getsize(file_info['path'])
        if size_bytes < 1024:
            file_size = f"{size_bytes} B"
        elif size_bytes < 1024*1024:
            file_size = f"{size_bytes/1024:.1f} KB"
        else:
            file_size = f"{size_bytes/1024/1024:.1f} MB"
        mime, _ = mimetypes.guess_type(file_info['filename'])
        if mime:
            if mime.startswith('image/'):
                file_type = 'Image'
                is_image = True
            elif mime.startswith('video/'):
                file_type = 'Video'
            elif mime.startswith('audio/'):
                file_type = 'Audio'
            elif mime == 'application/pdf':
                file_type = 'PDF Document'
            elif mime.startswith('text/'):
                file_type = 'Text File'
            else:
                file_type = mime
        else:
            file_type = 'Unknown'
    return render_template('file.html', file_info=file_info, file_id=file_id, file_size=file_size, size_bytes=size_bytes, file_type=file_type, is_image=is_image, APP_NAME=APP_NAME, session=session, is_admin=is_admin(session.get('username', '')))

@app.route('/download/<file_id>')
def download_file(file_id):
    file_info = file_db.get(file_id)
    if not file_info:
        flash('File not found!')
        return redirect(url_for('index'))
    return send_from_directory(app.config['UPLOAD_FOLDER'], file_info['unique_filename'], as_attachment=True, download_name=file_info['filename'])

@app.route('/delete/<file_id>', methods=['POST'])
def delete_file(file_id):
    if 'username' not in session:
        flash('Please login to delete files.')
        return redirect(url_for('login'))
    username = session['username']
    role = session.get('role', 'user')
    file_info = file_db.get(file_id)
    if not file_info:
        flash('File already deleted or not found.')
        return redirect(url_for('index'))
    # Only admin or owner can delete
    if role != 'admin' and file_info.get('owner') != username:
        flash('You do not have permission to delete this file.')
        return redirect(url_for('index'))

    # Check if this is a bundle
    if file_info.get('is_bundle'):
        # Delete all files in the bundle
        bundle_files = file_info.get('files', [])
        deleted_files = 0
        for bundle_file_id in bundle_files:
            bundle_file_info = file_db.get(bundle_file_id)
            if bundle_file_info:
                try:
                    if os.path.exists(bundle_file_info['path']):
                        os.remove(bundle_file_info['path'])
                        deleted_files += 1
                except Exception as e:
                    print(f'Error deleting bundle file {bundle_file_id}: {e}')
                # Remove file from database
                del file_db[bundle_file_id]
        # Remove bundle from database
        del file_db[file_id]
        flash(f'Bundle deleted successfully! ({deleted_files} files removed)')
    else:
        # Delete single file
        try:
            if os.path.exists(file_info['path']):
                os.remove(file_info['path'])
        except Exception as e:
            flash(f'Error deleting file: {e}')
            return redirect(url_for('index'))
        del file_db[file_id]
        flash('File deleted successfully!')

    # Save files database to file
    save_files_db(file_db)

    return redirect(url_for('index', show_all='1' if (role=='admin' and request.args.get('show_all')=='1') else '0'))

@app.route('/delete_all', methods=['POST'])
def delete_all():
    if 'username' not in session:
        flash('Please login to delete files.')
        return redirect(url_for('login'))
    username = session['username']
    role = session.get('role', 'user')
    show_all = request.args.get('show_all') == '1' if role == 'admin' else False
    if role == 'admin' and show_all:
        # Admin deletes all files
        to_delete = list(file_db.keys())
        try:
            # delete all files in the upload folder
            files_in_folder = os.listdir(app.config['UPLOAD_FOLDER'])
            for file in files_in_folder:
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], file)
                if os.path.isfile(file_path):
                    os.remove(file_path)
        except Exception as e:
            flash(f'Error deleting files: {e}')
    else:
        # User or admin in user mode: delete only own files
        to_delete = [fid for fid, info in file_db.items() if info.get('owner') == username]
    deleted_count = 0
    for fid in to_delete:
        file_info = file_db.get(fid)
        if file_info:
            try:
                if os.path.exists(file_info['path']):
                    os.remove(file_info['path'])
            except Exception:
                pass
            del file_db[fid]
            deleted_count += 1
    flash(f"Deleted {deleted_count} file(s) successfully!")

    # Save files database to file
    save_files_db(file_db)

    return redirect(url_for('index', show_all='1' if (role=='admin' and show_all) else '0'))

@app.route('/admin', methods=['GET', 'POST'])
def admin_dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))

    username = session['username']
    role = session.get('role', 'user')

    if role != 'admin':
        flash(f'Access denied for {username}. Admin privileges required.', 'error')
        return redirect(url_for('index'))

    if request.method == 'POST':
        try:
            SETTINGS['max_file_size_mb'] = max(1, int(request.form.get('max_file_size_mb', SETTINGS['max_file_size_mb'])))
            SETTINGS['max_files_per_bundle'] = max(1, int(request.form.get('max_files_per_bundle', SETTINGS['max_files_per_bundle'])))
            SETTINGS['total_server_storage_mb'] = max(100, int(request.form.get('total_server_storage_mb', SETTINGS.get('total_server_storage_mb', 102400))))
            SETTINGS['user_storage_limit_mb'] = max(10, int(request.form.get('user_storage_limit_mb', SETTINGS.get('user_storage_limit_mb', 1024))))
        except (TypeError, ValueError):
            flash('Invalid settings values.', 'error')
            return redirect(url_for('admin_dashboard'))

        # Update app name
        app_name = request.form.get('app_name', '').strip()
        if app_name:
            SETTINGS['app_name'] = app_name
            global APP_NAME
            APP_NAME = app_name

        SETTINGS['registration_open'] = bool(request.form.get('registration_open'))
        save_settings()
        flash('Settings updated successfully.', 'success')
        return redirect(url_for('admin_dashboard'))

    # Calculate storage statistics
    MAX_STORAGE_MB = SETTINGS.get('total_server_storage_mb', 102400)
    MAX_STORAGE_BYTES = MAX_STORAGE_MB * 1024 * 1024

    total_storage_used = 0
    file_type_stats = {}
    user_file_counts = {}
    user_storage_usage = {}
    files_by_date = {}

    for file_id, file_info in file_db.items():
        if file_info.get('is_bundle'):
            continue  # Skip bundles, count individual files

        # Calculate file size
        if os.path.exists(file_info['path']):
            file_size = os.path.getsize(file_info['path'])
            total_storage_used += file_size

            # File type statistics
            filename = file_info.get('filename', '')
            ext = filename.split('.')[-1].lower() if '.' in filename else 'no extension'
            file_type_stats[ext] = file_type_stats.get(ext, 0) + 1

            # User statistics
            owner = file_info.get('owner', 'unknown')
            user_file_counts[owner] = user_file_counts.get(owner, 0) + 1
            user_storage_usage[owner] = user_storage_usage.get(owner, 0) + file_size

            # Files by date (for timeline)
            date_str = file_info.get('timestamp', '').split(' ')[0]  # Get date part
            if date_str:
                files_by_date[date_str] = files_by_date.get(date_str, 0) + 1

    # Calculate storage percentage
    storage_percentage = (total_storage_used / MAX_STORAGE_BYTES) * 100

    # Format storage sizes
    def format_bytes(bytes_val):
        if bytes_val < 1024:
            return f"{bytes_val} B"
        elif bytes_val < 1024 * 1024:
            return f"{bytes_val/1024:.1f} KB"
        else:
            return f"{bytes_val/1024/1024:.1f} MB"

    total_storage_formatted = format_bytes(total_storage_used)
    remaining_storage = MAX_STORAGE_BYTES - total_storage_used
    remaining_storage_formatted = format_bytes(remaining_storage)

    # Get permanently deleted accounts (deleted_at > 30 days ago)
    permanently_deleted_users = []
    for uname, udata in USERS.items():
        if udata.get('deleted_at'):
            deleted_at = datetime.fromisoformat(udata['deleted_at'])
            deletion_date = deleted_at + timedelta(days=30)
            if datetime.now() > deletion_date:
                permanently_deleted_users.append({
                    'username': uname,
                    'deleted_at': deleted_at.strftime('%B %d, %Y'),
                    'days_ago': (datetime.now() - deleted_at).days,
                    'role': udata.get('role', 'user')
                })

    # Prepare data for charts
    dashboard_data = {
        'total_files': len([f for f in file_db.values() if not f.get('is_bundle')]),
        'total_bundles': len([f for f in file_db.values() if f.get('is_bundle')]),
        'total_users': len(USERS),
        'storage_used': total_storage_formatted,
        'storage_percentage': round(storage_percentage, 1),
        'remaining_storage': remaining_storage_formatted,
        'file_type_stats': file_type_stats,
        'user_file_counts': user_file_counts,
        'user_storage_usage': {k: format_bytes(v) for k, v in user_storage_usage.items()},
        'user_storage_bytes': user_storage_usage,
        'files_by_date': dict(sorted(files_by_date.items())),
        'max_storage_mb': MAX_STORAGE_MB,
        'permanently_deleted_users': permanently_deleted_users,
        'recovery_requests': recovery_requests
    }

    return render_template('admin_dashboard.html', data=dashboard_data, SETTINGS=SETTINGS, USERS=USERS, APP_NAME=APP_NAME)


def _require_admin():
    if 'username' not in session or session.get('role') != 'admin':
        flash('Admin access required.', 'error')
        return False
    return True


@app.route('/admin/create_user', methods=['POST'])
def admin_create_user():
    if not _require_admin():
        return redirect(url_for('login'))

    username = (request.form.get('username') or '').strip()
    password = request.form.get('password') or ''

    if not username or not password:
        flash('Username and password are required.', 'error')
        return redirect(url_for('admin_dashboard'))

    # Convert username to lowercase for case-insensitive comparison
    username_lower = username.lower()
    if username_lower in USERS:
        flash('User already exists.', 'error')
        return redirect(url_for('admin_dashboard'))

    USERS[username_lower] = {'password': password, 'role': 'user', 'storage_limit_mb': 50}
    save_users(USERS)
    flash(f'User {username_lower} created successfully.', 'success')
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/reset_password', methods=['POST'])
def admin_reset_password():
    if not _require_admin():
        return redirect(url_for('login'))

    username = (request.form.get('username') or '').strip()
    password = request.form.get('password') or ''

    if not username or not password:
        flash('Username and new password are required.', 'error')
        return redirect(url_for('admin_dashboard'))

    # Convert username to lowercase for case-insensitive lookup
    username_lower = username.lower()
    if username_lower not in USERS:
        flash('User does not exist.', 'error')
        return redirect(url_for('admin_dashboard'))

    USERS[username_lower]['password'] = password
    save_users(USERS)
    flash(f'Password reset for {username_lower}.', 'success')
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/update_storage_limit', methods=['POST'])
def admin_update_storage_limit():
    if not _require_admin():
        return redirect(url_for('login'))

    username = (request.form.get('username') or '').strip()
    storage_limit_mb = request.form.get('storage_limit_mb')

    if not username:
        flash('Username is required.', 'error')
        return redirect(url_for('admin_dashboard'))

    # Convert username to lowercase for case-insensitive lookup
    username_lower = username.lower()
    if username_lower not in USERS:
        flash('User does not exist.', 'error')
        return redirect(url_for('admin_dashboard'))

    try:
        storage_limit_mb = int(storage_limit_mb)
        if storage_limit_mb < 1:
            flash('Storage limit must be at least 1 MB.', 'error')
            return redirect(url_for('admin_dashboard'))
    except (TypeError, ValueError):
        flash('Invalid storage limit value.', 'error')
        return redirect(url_for('admin_dashboard'))

    USERS[username_lower]['storage_limit_mb'] = storage_limit_mb
    save_users(USERS)
    flash(f'Storage limit for {username_lower} updated to {storage_limit_mb} MB.', 'success')
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/delete_user', methods=['POST'])
def admin_delete_user():
    if not _require_admin():
        return redirect(url_for('login'))

    username = (request.form.get('username') or '').strip()

    if not username:
        flash('Username is required.', 'error')
        return redirect(url_for('admin_dashboard'))

    # Convert username to lowercase for case-insensitive lookup
    username_lower = username.lower()
    if username_lower not in USERS:
        flash('User does not exist.', 'error')
        return redirect(url_for('admin_dashboard'))

    if is_admin(username_lower):
        flash('Cannot delete an admin user.', 'error')
        return redirect(url_for('admin_dashboard'))

    # Remove user files and bundles
    ids_to_delete = []
    for fid, info in list(file_db.items()):
        if info.get('owner') == username_lower:
            ids_to_delete.append(fid)

    for fid in ids_to_delete:
        info = file_db.get(fid)
        if not info:
            continue
        if info.get('is_bundle'):
            for child_id in info.get('files', []):
                child_info = file_db.get(child_id)
                if child_info and os.path.exists(child_info['path']):
                    try:
                        os.remove(child_info['path'])
                    except OSError:
                        pass
                file_db.pop(child_id, None)
            file_db.pop(fid, None)
        else:
            if os.path.exists(info['path']):
                try:
                    os.remove(info['path'])
                except OSError:
                    pass
            file_db.pop(fid, None)

    save_files_db(file_db)

    USERS.pop(username_lower, None)
    save_users(USERS)
    flash(f'User {username_lower} deleted successfully.', 'success')
    flash(f'User {username} and their files were removed.', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/approve_recovery', methods=['POST'])
def admin_approve_recovery():
    """Admin route to approve recovery request"""
    if not _require_admin():
        return redirect(url_for('login'))

    username = (request.form.get('username') or '').strip()
    with_files = request.form.get('with_files', 'false').lower() == 'true'

    if not username:
        flash('Username is required.', 'error')
        return redirect(url_for('admin_dashboard'))

    # Convert username to lowercase
    username_lower = username.lower()
    
    # Check if recovery request exists
    if username_lower not in recovery_requests:
        flash('Recovery request not found.', 'error')
        return redirect(url_for('admin_dashboard'))
    
    # Check if user exists
    if username_lower not in USERS:
        flash('User does not exist.', 'error')
        return redirect(url_for('admin_dashboard'))

    user = USERS[username_lower]
    
    # Recover the account
    user['deleted_at'] = None
    save_users(USERS)
    
    # Handle files recovery if requested
    if with_files:
        # Note: Files were already deleted when account was deleted >30 days ago
        # This is just for future enhancement if files are kept
        flash(f'Account {username_lower} has been successfully recovered with file recovery attempted!', 'success')
    else:
        flash(f'Account {username_lower} has been successfully recovered without files!', 'success')
    
    # Remove the recovery request
    recovery_requests.pop(username_lower, None)
    save_recovery_requests(recovery_requests)
    
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/deny_recovery', methods=['POST'])
def admin_deny_recovery():
    """Admin route to deny recovery request"""
    if not _require_admin():
        return redirect(url_for('login'))

    username = (request.form.get('username') or '').strip()

    if not username:
        flash('Username is required.', 'error')
        return redirect(url_for('admin_dashboard'))

    # Convert username to lowercase
    username_lower = username.lower()
    
    # Check if recovery request exists
    if username_lower not in recovery_requests:
        flash('Recovery request not found.', 'error')
        return redirect(url_for('admin_dashboard'))
    
    # Remove the recovery request
    recovery_requests.pop(username_lower, None)
    save_recovery_requests(recovery_requests)
    
    flash(f'Recovery request for {username_lower} has been denied.', 'info')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/recover_deleted_user', methods=['POST'])
def admin_recover_deleted_user():
    """Admin route to recover permanently deleted accounts"""
    if not _require_admin():
        return redirect(url_for('login'))

    username = (request.form.get('username') or '').strip()
    with_files = request.form.get('with_files', 'false').lower() == 'true'

    if not username:
        flash('Username is required.', 'error')
        return redirect(url_for('admin_dashboard'))

    # Convert username to lowercase for case-insensitive lookup
    username_lower = username.lower()
    if username_lower not in USERS:
        flash('User does not exist.', 'error')
        return redirect(url_for('admin_dashboard'))

    user = USERS[username_lower]
    if not user.get('deleted_at'):
        flash('User account is not deleted.', 'error')
        return redirect(url_for('admin_dashboard'))

    # Check if 30 days have passed
    deleted_at = datetime.fromisoformat(user['deleted_at'])
    deletion_date = deleted_at + timedelta(days=30)
    
    if datetime.now() <= deletion_date:
        flash('User is still in the 30-day recovery period. They can recover their own account.', 'error')
        return redirect(url_for('admin_dashboard'))

    # Recover the account
    user['deleted_at'] = None
    save_users(USERS)
    
    # Handle files recovery message
    if with_files:
        flash(f'Account {username_lower} has been successfully recovered with file recovery attempted!', 'success')
    else:
        flash(f'Account {username_lower} has been successfully recovered without files!', 'success')
    
    return redirect(url_for('admin_dashboard'))

@app.errorhandler(413)
def file_too_large(e):
    flash('File is too large. Maximum allowed size is 40 MB.')
    return redirect(request.url)

if __name__ == '__main__':
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    if not os.path.exists(SESSION_FOLDER):
        os.makedirs(SESSION_FOLDER)
    if not os.path.exists(PROFILE_PICTURES_FOLDER):
        os.makedirs(PROFILE_PICTURES_FOLDER)
    app.run(debug=True)
