from flask import Flask, render_template, request, redirect, url_for, send_from_directory, flash, session
from flask_session import Session
from werkzeug.utils import secure_filename
import os
import uuid
from datetime import datetime
import mimetypes
import json

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Secure random key
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
SESSION_FOLDER = os.path.join(os.path.dirname(__file__), 'flask_session')

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

# In-memory file info storage: {file_id: {filename, path, timestamp}}
file_db = {}

# Helper to check admin
ADMIN_USERS = {'gdhanush270', 'pavi'}

# Application settings
SETTINGS = {
    'max_file_size_mb': 40,
    'max_files_per_bundle': 5,
    'registration_open': True
}

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

# Load users on startup
USERS = load_users()

# Load files database on startup
file_db = load_files_db()

def is_admin(username):
    return username in ADMIN_USERS

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
        if username in USERS:
            flash('Username already exists!', 'error')
            return render_template('register.html')
        USERS[username] = {'password': password, 'role': 'user'}
        save_users(USERS)
        print(f"User registered successfully: {username}")
        print(f"Current users: {list(USERS.keys())}")
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    print("Returning register.html template")
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username') or ""
        password = request.form.get('password') or ""
        print(f"Login attempt - Username: {username}, Password: {password}")
        user = USERS.get(username)
        print(f"User found: {user}")
        if user and user['password'] == password:
            session['username'] = username
            session['role'] = user['role']
            print(f"Login successful for: {username}")
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            print(f"Login failed for: {username}")
            flash('Invalid username or password!', 'error')
            return render_template('login.html')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('role', None)
    flash('Logged out successfully!', 'success')
    return redirect(url_for('login'))

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
    return render_template('index.html', files=user_files, is_admin=(role=='admin'), show_all=show_all)

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
        return render_template('bundle.html', bundle_info=file_info, files=bundle_files, file_id=file_id, bundle_size=bundle_size)

    file_size = None
    file_type = None
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
    return render_template('file.html', file_info=file_info, file_id=file_id, file_size=file_size, file_type=file_type)

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
        except (TypeError, ValueError):
            flash('Invalid settings values.', 'error')
            return redirect(url_for('admin_dashboard'))

        SETTINGS['registration_open'] = bool(request.form.get('registration_open'))
        flash('Settings updated successfully.', 'success')
        return redirect(url_for('admin_dashboard'))

    # Calculate storage statistics
    MAX_STORAGE_MB = 500
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
        'max_storage_mb': MAX_STORAGE_MB
    }

    return render_template('admin_dashboard.html', data=dashboard_data, SETTINGS=SETTINGS)


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

    if username in USERS:
        flash('User already exists.', 'error')
        return redirect(url_for('admin_dashboard'))

    USERS[username] = {'password': password, 'role': 'user'}
    save_users(USERS)
    flash(f'User {username} created successfully.', 'success')
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

    if username not in USERS:
        flash('User does not exist.', 'error')
        return redirect(url_for('admin_dashboard'))

    USERS[username]['password'] = password
    save_users(USERS)
    flash(f'Password reset for {username}.', 'success')
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/delete_user', methods=['POST'])
def admin_delete_user():
    if not _require_admin():
        return redirect(url_for('login'))

    username = (request.form.get('username') or '').strip()

    if not username:
        flash('Username is required.', 'error')
        return redirect(url_for('admin_dashboard'))

    if username not in USERS:
        flash('User does not exist.', 'error')
        return redirect(url_for('admin_dashboard'))

    if is_admin(username):
        flash('Cannot delete an admin user.', 'error')
        return redirect(url_for('admin_dashboard'))

    # Remove user files and bundles
    ids_to_delete = []
    for fid, info in list(file_db.items()):
        if info.get('owner') == username:
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

    USERS.pop(username, None)
    save_users(USERS)
    flash(f'User {username} and their files were removed.', 'success')
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
    app.run(debug=True)
