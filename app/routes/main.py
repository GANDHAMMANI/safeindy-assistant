"""
Main routes for SafeIndy Assistant
Handles homepage and basic navigation
"""

from flask import Blueprint, render_template, jsonify
from datetime import datetime

# Create blueprint
main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Homepage - Landing page for SafeIndy Assistant"""
    return render_template('index.html', 
                         current_time=datetime.now(),
                         page_title="SafeIndy Assistant")

@main_bp.route('/about')
def about():
    """About page - Information about the service"""
    features = [
        "24/7 Emergency Assistance",
        "Real-time Indianapolis Safety Data", 
        "Community Reporting System",
        "AI-Powered Safety Guidance",
        "Multi-language Support"
    ]
    
    return render_template('about.html',
                         features=features,
                         page_title="About SafeIndy")

@main_bp.route('/health')
def health_check():
    """Health check endpoint for monitoring"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'SafeIndy Assistant',
        'version': '1.0.0'
    })

@main_bp.route('/test')
def test_page():
    """Simple test page to verify Flask is working"""
    return """
    <h1>🚀 SafeIndy Assistant - Test Page</h1>
    <p>✅ Flask is running successfully!</p>
    <p>📍 Serving Indianapolis residents since 2025</p>
    <p>🕒 Server time: {}</p>
    <hr>
    <p><a href="/">← Back to Homepage</a></p>
    """.format(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))