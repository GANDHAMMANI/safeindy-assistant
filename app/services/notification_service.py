"""
Notification Service for SafeIndy Assistant
Handles emergency alerts via email and SMS
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import current_app
import json
from datetime import datetime
from typing import Dict, Optional
import requests

class NotificationService:
    def __init__(self):
        self.smtp_server = None
        self.initialize_email()
    
    def initialize_email(self):
        """Initialize email configuration"""
        try:
            self.mail_server = current_app.config.get('MAIL_SERVER')
            self.mail_port = current_app.config.get('MAIL_PORT')
            self.mail_username = current_app.config.get('MAIL_USERNAME')
            self.mail_password = current_app.config.get('MAIL_PASSWORD')
            self.emergency_email = current_app.config.get('EMERGENCY_ALERT_EMAIL')
            
            if all([self.mail_server, self.mail_username, self.mail_password, self.emergency_email]):
                print("✅ Emergency email notifications configured")
            else:
                print("⚠️ Emergency email not fully configured - missing credentials")
                
        except Exception as e:
            print(f"❌ Failed to initialize email service: {e}")
    
    def send_emergency_alert(self, user_message: str, location_data: Dict, session_id: str) -> Dict:
        """
        Send emergency alert email with user location
        
        Args:
            user_message: User's emergency message
            location_data: GPS coordinates and address info
            session_id: User's session ID
            
        Returns:
            Dict with success status and details
        """
        try:
            if not all([self.mail_username, self.mail_password, self.emergency_email]):
                return {
                    'success': False,
                    'error': 'Email configuration not complete'
                }
            
            # Create email content
            subject = "🚨 SAFEINDY EMERGENCY ALERT"
            
            # Format location info
            location_text = self._format_location_for_email(location_data)
            
            # Create HTML email body
            html_body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="background: #dc3545; color: white; padding: 20px; text-align: center;">
                    <h1>🚨 SafeIndy Emergency Alert</h1>
                    <p><strong>IMMEDIATE ATTENTION REQUIRED</strong></p>
                </div>
                
                <div style="padding: 20px;">
                    <h2>Emergency Details</h2>
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr style="background: #f8f9fa;">
                            <td style="padding: 10px; border: 1px solid #dee2e6; font-weight: bold;">Timestamp:</td>
                            <td style="padding: 10px; border: 1px solid #dee2e6;">{datetime.now().strftime('%Y-%m-%d %H:%M:%S EST')}</td>
                        </tr>
                        <tr>
                            <td style="padding: 10px; border: 1px solid #dee2e6; font-weight: bold;">Session ID:</td>
                            <td style="padding: 10px; border: 1px solid #dee2e6;">{session_id}</td>
                        </tr>
                        <tr style="background: #f8f9fa;">
                            <td style="padding: 10px; border: 1px solid #dee2e6; font-weight: bold;">User Message:</td>
                            <td style="padding: 10px; border: 1px solid #dee2e6;"><strong>"{user_message}"</strong></td>
                        </tr>
                    </table>
                    
                    <h2 style="color: #dc3545;">📍 User Location</h2>
                    {location_text}
                    
                    <div style="background: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; margin: 20px 0; border-radius: 5px;">
                        <h3 style="color: #856404; margin-top: 0;">⚠️ Action Required</h3>
                        <p>A SafeIndy Assistant user has indicated an emergency situation. Please verify the situation and take appropriate action if necessary.</p>
                        <p><strong>If this is a life-threatening emergency, contact 911 immediately.</strong></p>
                    </div>
                    
                    <h3>Indianapolis Emergency Contacts</h3>
                    <ul>
                        <li><strong>Emergency:</strong> 911</li>
                        <li><strong>Police Non-Emergency:</strong> 317-327-3811</li>
                        <li><strong>Mayor's Action Center:</strong> 317-327-4622</li>
                        <li><strong>Poison Control:</strong> 1-800-222-1222</li>
                    </ul>
                </div>
                
                <div style="background: #6c757d; color: white; padding: 10px; text-align: center; font-size: 12px;">
                    <p>This alert was generated by SafeIndy Assistant - Indianapolis Public Safety Chatbot</p>
                    <p>For system issues, check the application logs or contact the development team.</p>
                </div>
            </body>
            </html>
            """
            
            # Create plain text version
            text_body = f"""
SAFEINDY EMERGENCY ALERT
========================

IMMEDIATE ATTENTION REQUIRED

Emergency Details:
- Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S EST')}
- Session ID: {session_id}
- User Message: "{user_message}"

User Location:
{self._format_location_for_text(location_data)}

ACTION REQUIRED:
A SafeIndy Assistant user has indicated an emergency situation. 
Please verify the situation and take appropriate action if necessary.

If this is a life-threatening emergency, contact 911 immediately.

Indianapolis Emergency Contacts:
- Emergency: 911
- Police Non-Emergency: 317-327-3811
- Mayor's Action Center: 317-327-4622
- Poison Control: 1-800-222-1222

---
This alert was generated by SafeIndy Assistant
            """
            
            # Send email
            result = self._send_email(subject, html_body, text_body)
            
            if result['success']:
                print(f"🚨 Emergency alert sent for session {session_id}")
                return {
                    'success': True,
                    'message': 'Emergency alert sent successfully',
                    'timestamp': datetime.now().isoformat(),
                    'alert_id': f"emergency_{session_id}_{int(datetime.now().timestamp())}"
                }
            else:
                print(f"❌ Failed to send emergency alert: {result['error']}")
                return result
                
        except Exception as e:
            print(f"❌ Emergency alert error: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def send_system_notification(self, message: str, severity: str = 'info') -> Dict:
        """Send system notification email"""
        try:
            subject = f"SafeIndy System Notification - {severity.upper()}"
            
            html_body = f"""
            <html>
            <body style="font-family: Arial, sans-serif;">
                <div style="padding: 20px;">
                    <h2>SafeIndy System Notification</h2>
                    <p><strong>Severity:</strong> {severity.upper()}</p>
                    <p><strong>Timestamp:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S EST')}</p>
                    <div style="background: #f8f9fa; padding: 15px; border-left: 4px solid #007bff;">
                        {message}
                    </div>
                </div>
            </body>
            </html>
            """
            
            text_body = f"""
SafeIndy System Notification

Severity: {severity.upper()}
Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S EST')}

Message:
{message}
            """
            
            return self._send_email(subject, html_body, text_body)
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _send_email(self, subject: str, html_body: str, text_body: str) -> Dict:
        """Send email using SMTP"""
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.mail_username
            msg['To'] = self.emergency_email
            
            # Add both text and HTML parts
            text_part = MIMEText(text_body, 'plain')
            html_part = MIMEText(html_body, 'html')
            
            msg.attach(text_part)
            msg.attach(html_part)
            
            # Send email
            with smtplib.SMTP(self.mail_server, self.mail_port) as server:
                server.starttls()
                server.login(self.mail_username, self.mail_password)
                server.send_message(msg)
            
            return {
                'success': True,
                'message': 'Email sent successfully'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Email sending failed: {str(e)}'
            }
    
    def _format_location_for_email(self, location_data: Dict) -> str:
        """Format location data for HTML email"""
        if not location_data:
            return "<p><em>Location information not available</em></p>"
        
        html = "<table style='width: 100%; border-collapse: collapse;'>"
        
        if 'coordinates' in location_data:
            coords = location_data['coordinates']
            google_maps_url = f"https://www.google.com/maps?q={coords['lat']},{coords['lng']}"
            
            html += f"""
            <tr style="background: #f8f9fa;">
                <td style="padding: 10px; border: 1px solid #dee2e6; font-weight: bold;">GPS Coordinates:</td>
                <td style="padding: 10px; border: 1px solid #dee2e6;">
                    <a href="{google_maps_url}" target="_blank" style="color: #007bff;">
                        {coords['lat']:.6f}, {coords['lng']:.6f}
                    </a>
                </td>
            </tr>
            """
        
        if 'address' in location_data:
            html += f"""
            <tr>
                <td style="padding: 10px; border: 1px solid #dee2e6; font-weight: bold;">Address:</td>
                <td style="padding: 10px; border: 1px solid #dee2e6;">{location_data['address']}</td>
            </tr>
            """
        
        if 'accuracy' in location_data:
            html += f"""
            <tr style="background: #f8f9fa;">
                <td style="padding: 10px; border: 1px solid #dee2e6; font-weight: bold;">Location Accuracy:</td>
                <td style="padding: 10px; border: 1px solid #dee2e6;">±{location_data['accuracy']} meters</td>
            </tr>
            """
        
        html += "</table>"
        
        # Add map embed if coordinates available
        if 'coordinates' in location_data:
            coords = location_data['coordinates']
            html += f"""
            <div style="margin: 15px 0;">
                <h4>📍 Location on Map:</h4>
                <iframe 
                    width="100%" 
                    height="250" 
                    frameborder="0" 
                    src="https://www.google.com/maps/embed/v1/place?key={current_app.config.get('GOOGLE_MAPS_API_KEY', '')}&q={coords['lat']},{coords['lng']}&zoom=15"
                    style="border: 1px solid #dee2e6;">
                </iframe>
                <p style="font-size: 12px; color: #6c757d; margin-top: 5px;">
                    <a href="{google_maps_url}" target="_blank">Open in Google Maps</a>
                </p>
            </div>
            """
        
        return html
    
    def _format_location_for_text(self, location_data: Dict) -> str:
        """Format location data for plain text email"""
        if not location_data:
            return "Location information not available"
        
        text = ""
        
        if 'coordinates' in location_data:
            coords = location_data['coordinates']
            google_maps_url = f"https://www.google.com/maps?q={coords['lat']},{coords['lng']}"
            text += f"GPS Coordinates: {coords['lat']:.6f}, {coords['lng']:.6f}\n"
            text += f"Google Maps Link: {google_maps_url}\n"
        
        if 'address' in location_data:
            text += f"Address: {location_data['address']}\n"
        
        if 'accuracy' in location_data:
            text += f"Location Accuracy: ±{location_data['accuracy']} meters\n"
        
        return text
    
    def test_email_configuration(self) -> Dict:
        """Test email configuration"""
        try:
            test_subject = "SafeIndy Assistant - Email Test"
            test_message = f"""
            <html>
            <body>
                <h2>✅ Email Configuration Test</h2>
                <p>This is a test email from SafeIndy Assistant.</p>
                <p><strong>Timestamp:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S EST')}</p>
                <p>If you received this email, your emergency notification system is working correctly.</p>
            </body>
            </html>
            """
            
            text_message = f"""
SafeIndy Assistant - Email Test

This is a test email from SafeIndy Assistant.
Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S EST')}

If you received this email, your emergency notification system is working correctly.
            """
            
            result = self._send_email(test_subject, test_message, text_message)
            
            if result['success']:
                print("✅ Email test successful")
            else:
                print(f"❌ Email test failed: {result['error']}")
            
            return result
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Email test failed: {str(e)}'
            }