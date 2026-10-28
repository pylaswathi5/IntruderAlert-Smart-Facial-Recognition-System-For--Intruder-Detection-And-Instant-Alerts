import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from datetime import datetime
import logging

try:
    from config import EMAIL_CONFIG, DETECTION_SETTINGS
except ImportError:
    # Fallback if config.py doesn't exist
    from dotenv import load_dotenv
    load_dotenv()
    EMAIL_CONFIG = {
        'SMTP_SERVER': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
        'SMTP_PORT': int(os.getenv('SMTP_PORT', 587)),
        'EMAIL_ADDRESS': os.getenv('EMAIL_ADDRESS', 'email@gmail.com'),
        'EMAIL_PASSWORD': os.getenv('EMAIL_PASSWORD', 'your-16-character-app-password'),
        'ADMIN_EMAIL': os.getenv('ADMIN_EMAIL', os.getenv('EMAIL_ADDRESS', 'admin@gmail.com'))
    }
    DETECTION_SETTINGS = {
        'ENABLE_EMAIL_ALERTS': os.getenv('ENABLE_EMAIL_ALERTS', 'true').lower() == 'true'
    }

logger = logging.getLogger(__name__)

def send_intruder_alert(image_path, confidence=0.0):
    """
    Send email alert to admin when intruder is detected
    
    Args:
        image_path: Path to the intruder image
        confidence: Confidence score of the detection
    
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        # Check if email alerts are enabled
        if not DETECTION_SETTINGS.get('ENABLE_EMAIL_ALERTS', True):
            logger.info("Email alerts are disabled")
            return False
        
        # Check if email is configured
        if not EMAIL_CONFIG.get('EMAIL_ADDRESS') or not EMAIL_CONFIG.get('EMAIL_PASSWORD'):
            logger.warning("Email not configured. Please set EMAIL_ADDRESS and EMAIL_PASSWORD in .env file or config.py")
            return False
        
        if not os.path.exists(image_path):
            logger.error(f"Image file not found: {image_path}")
            return False
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = EMAIL_CONFIG['EMAIL_ADDRESS']
        msg['To'] = EMAIL_CONFIG['ADMIN_EMAIL']
        msg['Subject'] = f"🚨 INTRUDER DETECTED - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        # Email body
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h2 style="color: #d63031;">🚨 SECURITY ALERT: INTRUDER DETECTED</h2>
            <p><strong>Detection Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p><strong>Confidence Level:</strong> {confidence:.2%}</p>
            <hr>
            <p style="color: #636e72;">An unauthorized person has been detected by the facial recognition system.</p>
            <p style="color: #636e72;">Please review the attached image and take appropriate action.</p>
            <br>
            <p style="color: #636e72; font-size: 12px;">This is an automated alert from the Smart Facial Recognition System.</p>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(body, 'html'))
        
        # Attach image
        with open(image_path, 'rb') as f:
            img_data = f.read()
            image = MIMEImage(img_data, name=os.path.basename(image_path))
            msg.attach(image)
        
        # Send email
        server = smtplib.SMTP(EMAIL_CONFIG['SMTP_SERVER'], EMAIL_CONFIG['SMTP_PORT'])
        server.starttls()
        server.login(EMAIL_CONFIG['EMAIL_ADDRESS'], EMAIL_CONFIG['EMAIL_PASSWORD'])
        server.send_message(msg)
        server.quit()
        
        logger.info(f"Intruder alert email sent successfully to {EMAIL_CONFIG['ADMIN_EMAIL']}")
        return True
        
    except Exception as e:
        logger.error(f"Error sending email alert: {str(e)}")
        return False

def test_email_configuration():
    """Test email configuration"""
    try:
        server = smtplib.SMTP(EMAIL_CONFIG['SMTP_SERVER'], EMAIL_CONFIG['SMTP_PORT'])
        server.starttls()
        server.login(EMAIL_CONFIG['EMAIL_ADDRESS'], EMAIL_CONFIG['EMAIL_PASSWORD'])
        server.quit()
        return True
    except Exception as e:
        logger.error(f"Email configuration test failed: {str(e)}")
        return False

