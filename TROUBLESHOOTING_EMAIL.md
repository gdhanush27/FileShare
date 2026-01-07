# Email Troubleshooting Guide

## Quick Diagnostics

### 1. Check Email Configuration
When you start the Flask app, you should see:
```
==================================================
EMAIL CONFIGURATION CHECK
==================================================
MAIL_SERVER: smtp-mail.outlook.com
MAIL_PORT: 587
MAIL_USE_TLS: True
MAIL_USERNAME: filesharepro@outlook.com
MAIL_PASSWORD: ***SET***
==================================================
```

If you see `❌ NOT SET ❌` for MAIL_PASSWORD, the password is missing!

### 2. Test Email Sending
1. Start your Flask app
2. Login to your account
3. Visit: `http://localhost:5000/test_email`
4. Check the console output for detailed error messages
5. Check your inbox for the test email

## Common Issues & Solutions

### ❌ "MAIL_PASSWORD not configured"
**Problem:** Password is not set in `.env` file

**Solution:**
1. Open `.env` file
2. Update the line: `MAIL_PASSWORD=your_actual_password`
3. Restart the Flask application

### ❌ "Authentication failed" or "535 Authentication failed"
**Problem:** Outlook.com requires an App Password, not your regular password

**Solution - Get Outlook App Password:**

1. **Enable Two-Factor Authentication:**
   - Go to: https://account.microsoft.com/security
   - Click "Two-step verification"
   - Follow the setup wizard

2. **Create App Password:**
   - After 2FA is enabled, go back to Security settings
   - Look for "App passwords" or "Advanced security options"
   - Click "Create a new app password"
   - Copy the generated 16-character password (format: xxxx-xxxx-xxxx-xxxx)

3. **Update .env file:**
   ```
   MAIL_PASSWORD=xxxx-xxxx-xxxx-xxxx
   ```
   (Use the app password, including dashes or without - both work)

4. **Restart Flask app**

### ❌ "Connection refused" or "Timeout"
**Problem:** SMTP port blocked or wrong server

**Solutions:**
- Check firewall/antivirus settings
- Try port 25 instead of 587
- Verify internet connection
- Check if your ISP blocks SMTP ports

Update `.env`:
```
MAIL_PORT=25
```

### ❌ "SSL/TLS Error"
**Problem:** TLS configuration issue

**Solution:** Try disabling TLS and using SSL instead

Update `.env`:
```
MAIL_USE_TLS=False
MAIL_USE_SSL=True
```

And update `flask_app.py` configuration section:
```python
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'False') == 'True'
app.config['MAIL_USE_SSL'] = os.getenv('MAIL_USE_SSL', 'False') == 'True'
```

### ❌ Emails going to Spam/Junk folder
**Problem:** Email not verified or flagged as spam

**Solutions:**
1. Check Spam/Junk folder
2. Mark as "Not Spam"
3. Add sender to contacts
4. For production, use a verified domain with SPF/DKIM records

## Alternative: Using Gmail

If Outlook isn't working, try Gmail:

1. **Enable 2-Factor Authentication** on your Google account

2. **Create App Password:**
   - Go to: https://myaccount.google.com/apppasswords
   - Select "Mail" and your device
   - Copy the 16-character password

3. **Update .env file:**
   ```
   MAIL_SERVER=smtp.gmail.com
   MAIL_PORT=587
   MAIL_USE_TLS=True
   MAIL_USERNAME=your_email@gmail.com
   MAIL_PASSWORD=your_16_char_app_password
   MAIL_DEFAULT_SENDER=your_email@gmail.com
   ```

4. **Restart Flask app**

## Testing Checklist

- [ ] `.env` file exists in the same directory as `flask_app.py`
- [ ] `MAIL_PASSWORD` is set in `.env`
- [ ] Using App Password (not regular password)
- [ ] Two-factor authentication is enabled
- [ ] Flask app restarted after .env changes
- [ ] Visited `/test_email` route and checked console
- [ ] Checked spam/junk folder

## Still Not Working?

1. **Check Console Output:**
   - Look for detailed error messages when app starts
   - Check errors when visiting `/test_email`
   
2. **Verify Account Status:**
   - Make sure the email account isn't locked or suspended
   - Try logging into Outlook.com webmail
   
3. **Network Issues:**
   - Try from a different network
   - Disable VPN if using one
   - Check corporate firewall settings

4. **Debug Mode:**
   The app now prints detailed error messages including:
   - SMTP server connection status
   - Authentication errors
   - Full stack traces

All errors appear in the Flask console where you ran the app!

## Quick Fix Summary

**Most Common Solution:**
```bash
1. Go to https://account.microsoft.com/security
2. Enable Two-Factor Authentication
3. Create App Password
4. Update .env with app password
5. Restart Flask app
```

**Verify it works:**
```
Visit: http://localhost:5000/test_email
```
