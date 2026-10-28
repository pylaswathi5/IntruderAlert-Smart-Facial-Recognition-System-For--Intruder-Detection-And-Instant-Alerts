# Email Notification Setup Guide

This guide will help you configure email notifications for intruder detection alerts.

## Gmail Setup (Recommended)

### Step 1: Enable 2-Step Verification
1. Go to your Google Account settings: https://myaccount.google.com/
2. Navigate to **Security**
3. Enable **2-Step Verification** if not already enabled

### Step 2: Generate App Password
1. Go to: https://myaccount.google.com/apppasswords
2. Select **Mail** as the app
3. Select **Other (Custom name)** as the device
4. Enter "Face Recognition System" as the name
5. Click **Generate**
6. Copy the 16-character password (you'll need this)

### Step 3: Configure Environment Variables

Create a `.env` file in the project root:

```env
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_ADDRESS=your-email@gmail.com
EMAIL_PASSWORD=your-16-character-app-password
ADMIN_EMAIL=your-email@gmail.com
```

**Important:** Use the App Password, NOT your regular Gmail password!

## Other Email Providers

### Outlook/Hotmail
```env
SMTP_SERVER=smtp-mail.outlook.com
SMTP_PORT=587
EMAIL_ADDRESS=your-email@outlook.com
EMAIL_PASSWORD=your-password
ADMIN_EMAIL=your-email@outlook.com
```

### Yahoo Mail
```env
SMTP_SERVER=smtp.mail.yahoo.com
SMTP_PORT=587
EMAIL_ADDRESS=your-email@yahoo.com
EMAIL_PASSWORD=your-app-password
ADMIN_EMAIL=your-email@yahoo.com
```

### Custom SMTP Server
```env
SMTP_SERVER=your-smtp-server.com
SMTP_PORT=587
EMAIL_ADDRESS=your-email@domain.com
EMAIL_PASSWORD=your-password
ADMIN_EMAIL=admin@domain.com
```
## Email Configuration in email_utils.py
Make sure to configure the following details in your .env file:
1. Sender Email Address: The email address used to send alert notifications.
2. Email App Password: The 16-character Gmail App Password used to authenticate the sender account. Do not use your regular Gmail password.
3. Admin Email Address: The email address that receives intruder detection alerts.

## Testing Email Configuration

After setting up your `.env` file, you can test the email configuration by:

1. Running the application
2. Detecting an intruder (either via webcam or image upload)
3. Checking your email inbox for the alert


## Troubleshooting

### "Authentication failed" error
- Make sure you're using an App Password for Gmail, not your regular password
- Verify 2-Step Verification is enabled
- Check that EMAIL_ADDRESS and EMAIL_PASSWORD are correct in `.env`

### "Connection refused" error
- Check your firewall settings
- Verify SMTP_SERVER and SMTP_PORT are correct
- Some networks block SMTP ports - try using port 465 with SSL

### Email not sending
- Check the application logs for error messages
- Verify all environment variables are set correctly
- Make sure `ENABLE_EMAIL_ALERTS=true` in your `.env` file

## Security Notes

- Never commit your `.env` file to version control
- Keep your App Passwords secure
- Regularly rotate your App Passwords
- The `.env` file is already in `.gitignore`

## Disabling Email Alerts

If you want to disable email alerts temporarily, set in `.env`:
```env
ENABLE_EMAIL_ALERTS=false
```

The system will continue to detect intruders and play alarm sounds, but won't send emails.

