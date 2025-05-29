"""
Emergency routes for SafeIndy Assistant
Handles emergency services and critical safety information
"""

from flask import Blueprint, render_template, jsonify
from datetime import datetime

emergency_bp = Blueprint('emergency', __name__)

@emergency_bp.route('/')
def emergency_page():
    """Emergency services information page"""
    
    emergency_contacts = {
        'immediate': {
            'title': 'Immediate Emergency',
            'number': '911',
            'description': 'Police, Fire, Medical emergencies',
            'available': '24/7',
            'color': 'danger',
            'icon': 'fas fa-exclamation-triangle'
        },
        'police': {
            'title': 'Police Non-Emergency',
            'number': '317-327-3811',
            'description': 'IMPD reports, incidents, assistance',
            'available': '24/7',
            'color': 'primary',
            'icon': 'fas fa-shield-alt'
        },
        'city': {
            'title': 'City Services',
            'number': '317-327-4622',
            'description': 'Mayor\'s Action Center (311)',
            'available': 'Mon-Fri 8AM-5PM',
            'color': 'success',
            'icon': 'fas fa-city'
        },
        'poison': {
            'title': 'Poison Control',
            'number': '1-800-222-1222',
            'description': '24-hour poison help hotline',
            'available': '24/7',
            'color': 'warning',
            'icon': 'fas fa-skull-crossbones'
        }
    }
    
    return render_template('emergency.html',
                         emergency_contacts=emergency_contacts,
                         page_title="Emergency Services")

@emergency_bp.route('/api/contacts')
def emergency_contacts_api():
    """API endpoint for emergency contacts"""
    return jsonify({
        'emergency': '911',
        'police_non_emergency': '317-327-3811',
        'mayors_action_center': '317-327-4622',
        'poison_control': '1-800-222-1222',
        'text_911': 'Available in Indianapolis',
        'timestamp': datetime.now().isoformat()
    })

@emergency_bp.route('/panic')
def panic_button():
    """Panic button page with immediate emergency info"""
    return """
    <html>
    <head>
        <title>🚨 EMERGENCY - SafeIndy</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body { 
                background: #dc3545; color: white; text-align: center; 
                font-family: Arial; padding: 20px; font-size: 18px;
            }
            .emergency-number { 
                font-size: 4rem; font-weight: bold; margin: 20px 0;
                background: white; color: #dc3545; padding: 20px;
                border-radius: 10px; display: inline-block;
            }
            .contact { 
                background: rgba(255,255,255,0.1); margin: 10px 0; 
                padding: 15px; border-radius: 5px;
            }
        </style>
    </head>
    <body>
        <h1>🚨 EMERGENCY</h1>
        <div class="emergency-number">911</div>
        <p><strong>Call immediately for Police, Fire, or Medical emergencies</strong></p>
        <p>Text to 911 is also available in Indianapolis</p>
        
        <hr style="margin: 30px 0;">
        
        <div class="contact">
            <strong>Police Non-Emergency:</strong> 317-327-3811
        </div>
        <div class="contact">
            <strong>Poison Control:</strong> 1-800-222-1222
        </div>
        <div class="contact">
            <strong>City Services:</strong> 317-327-4622
        </div>
        
        <p style="margin-top: 30px;">
            <a href="/" style="color: white;">← Back to SafeIndy Assistant</a>
        </p>
    </body>
    </html>
    """