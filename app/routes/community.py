"""
Community routes for SafeIndy Assistant
Handles NeighborWatch and community safety features
"""

from flask import Blueprint, render_template, request, jsonify, session
from datetime import datetime
import uuid

community_bp = Blueprint('community', __name__)

@community_bp.route('/')
def community_page():
    """Community features overview page"""
    
    features = [
        {
            'title': 'Anonymous Reporting',
            'description': 'Report safety concerns without revealing your identity',
            'icon': 'fas fa-user-secret',
            'color': 'primary'
        },
        {
            'title': 'Neighborhood Alerts',
            'description': 'Get safety updates for your specific area',
            'icon': 'fas fa-bell',
            'color': 'warning'
        },
        {
            'title': 'Resource Finder',
            'description': 'Locate nearby emergency services and shelters',
            'icon': 'fas fa-map-marker-alt',
            'color': 'success'
        },
        {
            'title': 'Safety Analytics',
            'description': 'View neighborhood safety trends and statistics',
            'icon': 'fas fa-chart-bar',
            'color': 'info'
        }
    ]
    
    return render_template('community.html',
                         features=features,
                         page_title="Community Safety")

@community_bp.route('/report', methods=['GET', 'POST'])
def anonymous_report():
    """Anonymous reporting system"""
    
    if request.method == 'POST':
        try:
            data = request.get_json()
            
            report = {
                'id': str(uuid.uuid4()),
                'type': data.get('type', 'general'),
                'description': data.get('description', ''),
                'location': data.get('location', ''),
                'timestamp': datetime.now().isoformat(),
                'status': 'submitted'
            }
            
            # In a real app, we'd store this in Qdrant or forward to authorities
            # For now, just acknowledge receipt
            
            return jsonify({
                'success': True,
                'report_id': report['id'],
                'message': 'Report submitted anonymously. Thank you for helping keep Indianapolis safe.',
                'next_steps': 'Your report will be reviewed and forwarded to appropriate authorities if action is needed.'
            })
            
        except Exception as e:
            return jsonify({'error': f'Failed to submit report: {str(e)}'}), 500
    
    # GET request - show reporting form
    report_types = [
        'Suspicious Activity',
        'Safety Hazard',
        'Drug Activity', 
        'Vandalism',
        'Noise Complaint',
        'Street Issues',
        'Other'
    ]
    
    return render_template('report_form.html',
                         report_types=report_types,
                         page_title="Anonymous Report")

@community_bp.route('/resources')
def local_resources():
    """Find local community resources"""
    
    # Mock data for Indianapolis resources
    resources = {
        'emergency_shelters': [
            {'name': 'Wheeler Mission', 'address': '245 N Delaware St', 'phone': '317-635-3575'},
            {'name': 'Salvation Army', 'address': '1821 E 16th St', 'phone': '317-637-5551'}
        ],
        'hospitals': [
            {'name': 'IU Health Methodist', 'address': '1701 N Senate Blvd', 'phone': '317-962-2000'},
            {'name': 'Eskenazi Hospital', 'address': '720 Eskenazi Ave', 'phone': '317-880-0000'}
        ],
        'police_stations': [
            {'name': 'IMPD North District', 'address': '3120 E 30th St', 'phone': '317-327-3811'},
            {'name': 'IMPD Downtown', 'address': '50 N Alabama St', 'phone': '317-327-3811'}
        ]
    }
    
    return jsonify({
        'resources': resources,
        'timestamp': datetime.now().isoformat(),
        'coverage_area': 'Indianapolis, IN'
    })

@community_bp.route('/alerts')
def community_alerts():
    """Community safety alerts"""
    
    # Mock alerts for demonstration
    alerts = [
        {
            'id': '1',
            'type': 'weather',
            'title': 'Severe Weather Watch',
            'message': 'Thunderstorm watch in effect for Indianapolis area until 8 PM',
            'timestamp': datetime.now().isoformat(),
            'priority': 'medium'
        },
        {
            'id': '2', 
            'type': 'traffic',
            'title': 'Road Closure',
            'message': 'I-65 southbound closed due to accident near downtown',
            'timestamp': datetime.now().isoformat(),
            'priority': 'low'
        }
    ]
    
    return jsonify({
        'alerts': alerts,
        'count': len(alerts),
        'last_updated': datetime.now().isoformat()
    })