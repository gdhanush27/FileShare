# Email Features Setup Guide

## Features Added

1. **Password Recovery via Email**
   - Users can reset their password using their registered email
   - Forgot password link on login page
   - Secure token-based password reset (expires in 1 hour)

2. **Email Verification**
   - New users receive a verification email upon registration
   - Users must verify their email before uploading files
   - Verification links expire in 24 hours
   - Users can resend verification emails from their profile page

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Email Settings

#### Option A: Using Outlook/Hotmail (Recommended - Free)

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit the `.env` file and add your Outlook password:
   ```
   MAIL_USERNAME=filesharepro@outlook.com
   MAIL_PASSWORD=your_actual_password_here
   ```

3. **For better security, use an App Password:**
   - Go to https://account.microsoft.com/security
   - Enable two-factor authentication (if not already enabled)
   - Create an app-specific password for this application
   - Use the app password in the `.env` file instead of your regular password

#### Option B: Using Gmail (Alternative - Free)

If you prefer Gmail, update your `.env` file:

```
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your_gmail@gmail.com
MAIL_PASSWORD=your_app_password_here
MAIL_DEFAULT_SENDER=your_gmail@gmail.com
```

**Gmail App Password Setup:**
1. Go to https://myaccount.google.com/security
2. Enable 2-Step Verification
3. Go to "App passwords" section
4. Generate a new app password for "Mail"
5. Use this 16-character password in your `.env` file

### 3. Security Notes

- **NEVER commit the `.env` file to version control** (it's already in `.gitignore`)
- Keep your email credentials secure
- Use app-specific passwords instead of regular account passwords
- The `.env.example` file is safe to commit and serves as a template

### 4. Testing the Features

#### Test Password Recovery:
1. Go to login page
2. Click "Forgot Password?"
3. Enter your registered email
4. Check your email for the reset link
5. Click the link and set a new password

#### Test Email Verification:
1. Register a new account
2. Check your email for the verification link
3. Click the link to verify your email
4. Try uploading a file (should work after verification)

#### Test Resend Verification:
1. Login with an unverified account
2. Go to your profile page
3. Click "Resend Verification Email"
4. Check your email for the new verification link

### 5. Troubleshooting

**Email not sending:**
- Check your `.env` file has the correct credentials
- Verify your email account allows SMTP access
- Check if two-factor authentication is properly configured
- Look at the console output for error messages

**"Authentication failed" error:**
- Make sure you're using an app-specific password, not your regular password
- Verify the MAIL_USERNAME matches the sender email
- Check if your email provider requires additional security settings

**Verification/Reset links not working:**
- Links expire after set time (1 hour for password reset, 24 hours for email verification)
- Request a new link if the old one expired
- Make sure the URL is being copied completely

### 6. Customization

You can customize the email templates in [flask_app.py](flask_app.py):
- `send_password_reset_email()` - Password reset email template
- `send_verification_email()` - Email verification template

Look for the `html_body` variable in each function to modify the email design and content.

## Features Overview

### Password Recovery Flow:
1. User clicks "Forgot Password?" on login page
2. User enters their registered email
3. System generates a secure token and sends reset email
4. User clicks the link in email
5. User enters new password
6. Password is updated and user can login

### Email Verification Flow:
1. User registers a new account
2. System generates verification token and sends email
3. User clicks verification link in email
4. Email is marked as verified
5. User can now upload files

### Security Features:
- Tokens use cryptographically secure random generation
- Password reset tokens expire in 1 hour
- Email verification tokens expire in 24 hours
- Email enumeration protection (same message for valid/invalid emails)
- Tokens are single-use and deleted after successful use

## Support

If you encounter any issues:
1. Check the console output for error messages
2. Verify your `.env` configuration
3. Ensure all dependencies are installed
4. Check your email provider's SMTP documentation
