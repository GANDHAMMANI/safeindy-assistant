/**
 * SafeIndy Assistant - Main JavaScript
 * Handles general functionality and interactions
 */

// Global SafeIndy object
window.SafeIndy = {
    version: '1.0.0',
    debug: true,
    
    // Emergency contacts for quick access
    emergencyContacts: {
        emergency: '911',
        police: '317-327-3811',
        city: '317-327-4622',
        poison: '1-800-222-1222'
    },
    
    // Initialize the application
    init: function() {
        console.log('🚀 SafeIndy Assistant initialized');
        this.setupEventListeners();
        this.checkSystemStatus();
        this.setupEmergencyFeatures();
    },
    
    // Set up event listeners
    setupEventListeners: function() {
        // Emergency button clicks
        document.addEventListener('click', function(e) {
            if (e.target.classList.contains('emergency-btn')) {
                SafeIndy.handleEmergencyClick(e);
            }
            
            if (e.target.classList.contains('call-btn')) {
                SafeIndy.handlePhoneCall(e);
            }
        });
        
        // Keyboard shortcuts
        document.addEventListener('keydown', function(e) {
            // Ctrl/Cmd + E for emergency
            if ((e.ctrlKey || e.metaKey) && e.key === 'e') {
                e.preventDefault();
                SafeIndy.showEmergencyInfo();
            }
        });
        
        // Page visibility change (for notifications)
        document.addEventListener('visibilitychange', function() {
            if (document.hidden) {
                SafeIndy.onPageHidden();
            } else {
                SafeIndy.onPageVisible();
            }
        });
    },
    
    // Check system status
    checkSystemStatus: function() {
        fetch('/api/status')
            .then(response => response.json())
            .then(data => {
                if (data.status === 'healthy') {
                    console.log('✅ System status: Healthy');
                    this.updateStatusIndicator('healthy');
                } else {
                    console.warn('⚠️ System status: Degraded');
                    this.updateStatusIndicator('degraded');
                }
            })
            .catch(error => {
                console.error('❌ System status check failed:', error);
                this.updateStatusIndicator('error');
            });
    },
    
    // Update status indicator
    updateStatusIndicator: function(status) {
        const indicator = document.getElementById('status-indicator');
        if (indicator) {
            indicator.className = `status-indicator status-${status}`;
            indicator.title = `System Status: ${status}`;
        }
    },
    
    // Handle emergency button clicks
    handleEmergencyClick: function(event) {
        event.preventDefault();
        const action = event.target.dataset.action;
        
        switch(action) {
            case 'call-911':
                this.confirmEmergencyCall('911');
                break;
            case 'call-police':
                this.confirmEmergencyCall('317-327-3811');
                break;
            case 'show-panic':
                this.showPanicScreen();
                break;
            default:
                this.showEmergencyInfo();
        }
    },
    
    // Handle phone call buttons
    handlePhoneCall: function(event) {
        const number = event.target.dataset.number;
        if (number) {
            // Create tel: link
            window.location.href = `tel:${number}`;
        }
    },
    
    // Confirm emergency call
    confirmEmergencyCall: function(number) {
        const isEmergency = number === '911';
        const message = isEmergency 
            ? 'Call 911 for immediate emergency assistance?'
            : `Call ${number} for non-emergency assistance?`;
            
        if (confirm(message)) {
            window.location.href = `tel:${number}`;
        }
    },
    
    // Show emergency information
    showEmergencyInfo: function() {
        const modal = this.createModal('emergency-info', 'Emergency Contacts', `
            <div class="emergency-contacts">
                <div class="emergency-item urgent">
                    <i class="fas fa-exclamation-triangle"></i>
                    <div>
                        <h5>Emergency: 911</h5>
                        <p>Police, Fire, Medical</p>
                        <button class="btn btn-danger btn-sm call-btn" data-number="911">
                            <i class="fas fa-phone"></i> Call Now
                        </button>
                    </div>
                </div>
                
                <div class="emergency-item">
                    <i class="fas fa-shield-alt"></i>
                    <div>
                        <h5>Police Non-Emergency</h5>
                        <p>317-327-3811</p>
                        <button class="btn btn-primary btn-sm call-btn" data-number="317-327-3811">
                            <i class="fas fa-phone"></i> Call
                        </button>
                    </div>
                </div>
                
                <div class="emergency-item">
                    <i class="fas fa-city"></i>
                    <div>
                        <h5>City Services (311)</h5>
                        <p>317-327-4622</p>
                        <button class="btn btn-success btn-sm call-btn" data-number="317-327-4622">
                            <i class="fas fa-phone"></i> Call
                        </button>
                    </div>
                </div>
            </div>
        `);
        
        document.body.appendChild(modal);
        setTimeout(() => modal.classList.add('show'), 10);
    },
    
    // Show panic screen
    showPanicScreen: function() {
        window.location.href = '/emergency/panic';
    },
    
    // Create modal dialog
    createModal: function(id, title, content) {
        const existingModal = document.getElementById(id);
        if (existingModal) {
            existingModal.remove();
        }
        
        const modal = document.createElement('div');
        modal.id = id;
        modal.className = 'modal-overlay';
        modal.innerHTML = `
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">${title}</h5>
                        <button type="button" class="modal-close" onclick="this.closest('.modal-overlay').remove()">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                    <div class="modal-body">
                        ${content}
                    </div>
                </div>
            </div>
        `;
        
        // Close on backdrop click
        modal.addEventListener('click', function(e) {
            if (e.target === modal) {
                modal.remove();
            }
        });
        
        return modal;
    },
    
    // Setup emergency features
    setupEmergencyFeatures: function() {
        // Add emergency styles
        const style = document.createElement('style');
        style.textContent = `
            .modal-overlay {
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0,0,0,0.5);
                display: flex;
                align-items: center;
                justify-content: center;
                z-index: 1050;
                opacity: 0;
                transition: opacity 0.3s ease;
            }
            
            .modal-overlay.show {
                opacity: 1;
            }
            
            .modal-dialog {
                background: white;
                border-radius: 12px;
                padding: 0;
                max-width: 500px;
                width: 90%;
                max-height: 90vh;
                overflow-y: auto;
                box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            }
            
            .modal-header {
                padding: 1.5rem;
                border-bottom: 1px solid #dee2e6;
                background: #f8f9fa;
                border-radius: 12px 12px 0 0;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            
            .modal-title {
                margin: 0;
                font-weight: 600;
            }
            
            .modal-close {
                background: none;
                border: none;
                font-size: 1.5rem;
                cursor: pointer;
                color: #6c757d;
                padding: 0;
                width: 30px;
                height: 30px;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            
            .modal-body {
                padding: 1.5rem;
            }
            
            .emergency-contacts {
                display: flex;
                flex-direction: column;
                gap: 1rem;
            }
            
            .emergency-item {
                display: flex;
                align-items: center;
                gap: 1rem;
                padding: 1rem;
                border-radius: 8px;
                background: #f8f9fa;
            }
            
            .emergency-item.urgent {
                background: #fff5f5;
                border: 2px solid #dc3545;
            }
            
            .emergency-item i {
                font-size: 1.5rem;
                width: 40px;
                text-align: center;
            }
            
            .emergency-item div {
                flex: 1;
            }
            
            .emergency-item h5 {
                margin: 0 0 0.25rem 0;
                font-size: 1.1rem;
            }
            
            .emergency-item p {
                margin: 0;
                color: #6c757d;
                font-size: 0.9rem;
            }
            
            .status-indicator {
                width: 12px;
                height: 12px;
                border-radius: 50%;
                display: inline-block;
                margin-right: 8px;
            }
            
            .status-healthy { background: #28a745; }
            .status-degraded { background: #ffc107; }
            .status-error { background: #dc3545; }
        `;
        document.head.appendChild(style);
    },
    
    // Handle page visibility changes
    onPageHidden: function() {
        console.log('Page hidden - pausing non-critical operations');
    },
    
    onPageVisible: function() {
        console.log('Page visible - resuming operations');
        this.checkSystemStatus();
    },
    
    // Utility functions
    utils: {
        // Format phone number
        formatPhoneNumber: function(number) {
            const cleaned = number.replace(/\D/g, '');
            if (cleaned.length === 10) {
                return `(${cleaned.slice(0,3)}) ${cleaned.slice(3,6)}-${cleaned.slice(6)}`;
            }
            return number;
        },
        
        // Show notification
        showNotification: function(message, type = 'info') {
            const notification = document.createElement('div');
            notification.className = `alert alert-${type} alert-dismissible position-fixed`;
            notification.style.cssText = 'top: 20px; right: 20px; z-index: 1060; min-width: 300px;';
            notification.innerHTML = `
                ${message}
                <button type="button" class="btn-close" onclick="this.parentElement.remove()"></button>
            `;
            
            document.body.appendChild(notification);
            
            // Auto-remove after 5 seconds
            setTimeout(() => {
                if (notification.parentElement) {
                    notification.remove();
                }
            }, 5000);
        },
        
        // Debounce function
        debounce: function(func, wait) {
            let timeout;
            return function executedFunction(...args) {
                const later = () => {
                    clearTimeout(timeout);
                    func(...args);
                };
                clearTimeout(timeout);
                timeout = setTimeout(later, wait);
            };
        },
        
        // Get current location (if permission granted)
        getCurrentLocation: function() {
            return new Promise((resolve, reject) => {
                if (!navigator.geolocation) {
                    reject(new Error('Geolocation not supported'));
                    return;
                }
                
                navigator.geolocation.getCurrentPosition(
                    position => resolve({
                        lat: position.coords.latitude,
                        lng: position.coords.longitude,
                        accuracy: position.coords.accuracy
                    }),
                    error => reject(error),
                    { timeout: 10000, enableHighAccuracy: true }
                );
            });
        }
    }
};

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    SafeIndy.init();
});

// Handle errors globally
window.addEventListener('error', function(e) {
    console.error('Global error:', e.error);
    if (SafeIndy.debug) {
        SafeIndy.utils.showNotification('An error occurred. Please refresh the page if issues persist.', 'warning');
    }
});

// Export for use in other scripts
window.SafeIndy = SafeIndy;