"""
Configuration file for email settings
Update these values or set them as environment variables
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Email Configuratio                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                n
# For Gmail, you need to use an "App Password" instead of your regular password
# Go to: Google Account > Security > 2-Step Verification > App Passwords

EMAIL_CONFIG = {
    'SMTP_SERVER': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
    'SMTP_PORT': int(os.getenv('SMTP_PORT', 587)),
    'EMAIL_ADDRESS': os.getenv('EMAIL_ADDRESS', ''),
    'EMAIL_PASSWORD': os.getenv('EMAIL_PASSWORD', ''),
    'ADMIN_EMAIL': os.getenv('ADMIN_EMAIL', os.getenv('EMAIL_ADDRESS', ''))
}

# Detection Settings
DETECTION_SETTINGS = {
    'ALERT_COOLDOWN': int(os.getenv('ALERT_COOLDOWN', 30)),  # seconds between alerts
    'ENABLE_EMAIL_ALERTS': os.getenv('ENABLE_EMAIL_ALERTS', 'true').lower() == 'true',
    'ENABLE_ALARM_SOUND': os.getenv('ENABLE_ALARM_SOUND', 'true').lower() == 'true'
}

