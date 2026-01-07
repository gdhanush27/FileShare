"""
Configuration module for FileShare Pro
Handles email and application settings
"""
import json
import os

# Configuration file path
CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'settings.json')

# Default email configuration
EMAIL_CONFIG = {
    'MAIL_SERVER': 'smtp.example.com',
    'MAIL_PORT': 587,
    'MAIL_USE_TLS': True,
    'MAIL_USERNAME': 'your-email@example.com',
    'MAIL_PASSWORD': 'your-password-here',
    'MAIL_DEFAULT_SENDER': 'your-email@example.com'
}

def load_config():
    """Load email configuration from settings.json"""
    global EMAIL_CONFIG
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                settings = json.load(f)
                # Update EMAIL_CONFIG with values from settings.json if they exist
                if 'email' in settings:
                    EMAIL_CONFIG.update(settings['email'])
        except (json.JSONDecodeError, IOError):
            pass
    return EMAIL_CONFIG

def save_config(email_config):
    """Save email configuration to settings.json"""
    global EMAIL_CONFIG
    EMAIL_CONFIG = email_config
    
    # Load existing settings
    settings = {}
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                settings = json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    
    # Update email section
    settings['email'] = email_config
    
    # Save back to file
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(settings, f, indent=2)
        return True
    except IOError:
        return False

def get_mail_config():
    """Get Flask-Mail compatible configuration dictionary"""
    return {
        'MAIL_SERVER': EMAIL_CONFIG.get('MAIL_SERVER', 'smtp.example.com'),
        'MAIL_PORT': int(EMAIL_CONFIG.get('MAIL_PORT', 587)),
        'MAIL_USE_TLS': EMAIL_CONFIG.get('MAIL_USE_TLS', True),
        'MAIL_USERNAME': EMAIL_CONFIG.get('MAIL_USERNAME', ''),
        'MAIL_PASSWORD': EMAIL_CONFIG.get('MAIL_PASSWORD', ''),
        'MAIL_DEFAULT_SENDER': EMAIL_CONFIG.get('MAIL_DEFAULT_SENDER', '')
    }

# Load configuration on module import
load_config()
