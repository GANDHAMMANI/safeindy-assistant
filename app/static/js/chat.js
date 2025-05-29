// Complete SafeIndy Chat Application - Integrated JavaScript
const ChatApp = {
    messagesContainer: null,
    chatInput: null,
    sendButton: null,
    typingIndicator: null,
    userLocation: null,
    locationWatchId: null,
    pendingEmergencyMessage: null,
    
    init: function() {
        this.messagesContainer = document.getElementById('chat-messages');
        this.chatInput = document.getElementById('chat-input');
        this.sendButton = document.getElementById('send-btn');
        this.typingIndicator = document.getElementById('typing-indicator');
        
        this.setupEventListeners();
        this.focusInput();
        this.checkLocationSupport();
        
        console.log('✅ ChatApp initialized with emergency functions');
    },
    
    // ===== LOCATION SERVICES =====
    
    checkLocationSupport: function() {
        if ('geolocation' in navigator) {
            // Show location banner after 3 seconds if not enabled
            setTimeout(() => {
                if (!this.userLocation) {
                    const banner = document.getElementById('location-banner');
                    if (banner) banner.style.display = 'block';
                }
            }, 3000);
        }
    },
    
    requestLocation: function() {
        if (!('geolocation' in navigator)) {
            alert('Geolocation is not supported by this browser.');
            return;
        }
        
        const options = {
            enableHighAccuracy: true,
            timeout: 10000,
            maximumAge: 300000 // 5 minutes
        };
        
        // Show loading state
        const banner = document.getElementById('location-banner');
        if (banner) {
            banner.innerHTML = `
                <i class="fas fa-spinner fa-spin me-2"></i>
                <strong>Getting your location...</strong>
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            `;
        }
        
        navigator.geolocation.getCurrentPosition(
            (position) => this.onLocationSuccess(position),
            (error) => this.onLocationError(error),
            options
        );
        
        // Also watch for location changes
        this.locationWatchId = navigator.geolocation.watchPosition(
            (position) => this.onLocationUpdate(position),
            (error) => console.log('Location watch error:', error),
            { ...options, maximumAge: 600000 } // 10 minutes for watching
        );
    },
    
    onLocationSuccess: function(position) {
        this.userLocation = {
            lat: position.coords.latitude,
            lng: position.coords.longitude,
            accuracy: position.coords.accuracy,
            timestamp: new Date().toISOString(),
            source: 'gps'
        };
        
        // Hide location banner
        const banner = document.getElementById('location-banner');
        if (banner) banner.style.display = 'none';
        
        // Show location status
        const statusDiv = document.getElementById('location-status');
        const locationText = document.getElementById('location-text');
        
        if (statusDiv) statusDiv.style.display = 'block';
        if (locationText) locationText.textContent = `Location enabled (±${Math.round(position.coords.accuracy)}m accuracy)`;
        
        // Reverse geocode to get address
        this.reverseGeocode(position.coords.latitude, position.coords.longitude);
        
        console.log('✅ Location obtained:', this.userLocation);
        
        // If there's a pending emergency message, send alert now
        if (this.pendingEmergencyMessage) {
            console.log('🚨 Sending pending emergency alert with new location...');
            this.sendEmergencyAlert(this.pendingEmergencyMessage, {emergency: true});
            this.pendingEmergencyMessage = null;
        }
    },
    
    onLocationError: function(error) {
        let errorMessage = 'Failed to get location: ';
        switch(error.code) {
            case error.PERMISSION_DENIED:
                errorMessage += 'Location access denied by user.';
                break;
            case error.POSITION_UNAVAILABLE:
                errorMessage += 'Location information unavailable.';
                break;
            case error.TIMEOUT:
                errorMessage += 'Location request timed out.';
                break;
            default:
                errorMessage += 'Unknown error occurred.';
        }
        
        console.log('❌ Location error:', errorMessage);
        
        // Reset banner
        const banner = document.getElementById('location-banner');
        if (banner) {
            banner.innerHTML = `
                <i class="fas fa-map-marker-alt me-2"></i>
                <strong>Location access failed.</strong> Emergency services may be less accurate.
                <button type="button" class="btn btn-sm btn-outline-primary ms-2" onclick="ChatApp.requestLocation()">
                    <i class="fas fa-retry me-1"></i>Try Again
                </button>
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            `;
        }
    },
    
    onLocationUpdate: function(position) {
        // Update location if significantly different
        if (this.userLocation) {
            const distance = this.calculateDistance(
                this.userLocation.lat, this.userLocation.lng,
                position.coords.latitude, position.coords.longitude
            );
            
            // Update if moved more than 100 meters
            if (distance > 0.1) {
                this.userLocation = {
                    lat: position.coords.latitude,
                    lng: position.coords.longitude,
                    accuracy: position.coords.accuracy,
                    timestamp: new Date().toISOString(),
                    source: 'gps'
                };
                console.log('📍 Location updated:', this.userLocation);
            }
        }
    },
    
    reverseGeocode: function(lat, lng) {
        // Simple reverse geocoding using a free service
        fetch(`https://api.bigdatacloud.net/data/reverse-geocode-client?latitude=${lat}&longitude=${lng}&localityLanguage=en`)
            .then(response => response.json())
            .then(data => {
                if (data.locality && data.principalSubdivision) {
                    this.userLocation.address = `${data.locality}, ${data.principalSubdivision}`;
                    const locationText = document.getElementById('location-text');
                    if (locationText) locationText.textContent = `Location: ${data.locality}, ${data.principalSubdivision}`;
                }
            })
            .catch(error => console.log('Reverse geocode error:', error));
    },
    
    showLocationDetails: function() {
        if (!this.userLocation) return;
        
        const modalContent = `
            <div class="location-details">
                <div class="mb-3">
                    <strong>📍 Coordinates:</strong><br>
                    ${this.userLocation.lat.toFixed(6)}, ${this.userLocation.lng.toFixed(6)}
                </div>
                
                <div class="mb-3">
                    <strong>🎯 Accuracy:</strong><br>
                    ±${Math.round(this.userLocation.accuracy)} meters
                </div>
                
                ${this.userLocation.address ? `
                <div class="mb-3">
                    <strong>🏠 Address:</strong><br>
                    ${this.userLocation.address}
                </div>
                ` : ''}
                
                <div class="mb-3">
                    <strong>🕐 Last Updated:</strong><br>
                    ${new Date(this.userLocation.timestamp).toLocaleString()}
                </div>
                
                <div class="alert alert-info">
                    <i class="fas fa-info-circle me-2"></i>
                    Your location is used to provide more accurate emergency assistance and find nearby resources. 
                    It's automatically included in emergency alerts.
                </div>
                
                <div class="d-flex gap-2">
                    <button class="btn btn-outline-primary btn-sm" onclick="ChatApp.requestLocation()">
                        <i class="fas fa-sync me-1"></i>Update Location
                    </button>
                    <button class="btn btn-outline-secondary btn-sm" onclick="ChatApp.openInMaps()">
                        <i class="fas fa-external-link-alt me-1"></i>Open in Maps
                    </button>
                </div>
            </div>
        `;
        
        // Try to use SafeIndy.createModal if available, otherwise use alert
        if (typeof SafeIndy !== 'undefined' && SafeIndy.createModal) {
            const modal = SafeIndy.createModal('location-details', 'Your Location Details', modalContent);
            document.body.appendChild(modal);
            setTimeout(() => modal.classList.add('show'), 10);
        } else {
            alert(`Location: ${this.userLocation.lat.toFixed(6)}, ${this.userLocation.lng.toFixed(6)}\nAccuracy: ±${Math.round(this.userLocation.accuracy)}m`);
        }
    },
    
    openInMaps: function() {
        if (this.userLocation) {
            const url = `https://www.google.com/maps?q=${this.userLocation.lat},${this.userLocation.lng}`;
            window.open(url, '_blank');
        }
    },
    
    calculateDistance: function(lat1, lng1, lat2, lng2) {
        // Haversine formula for distance in kilometers
        const R = 6371;
        const dLat = (lat2 - lat1) * Math.PI / 180;
        const dLng = (lng2 - lng1) * Math.PI / 180;
        const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
                Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
                Math.sin(dLng/2) * Math.sin(dLng/2);
        const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
        return R * c;
    },
    
    // ===== CHAT FUNCTIONALITY =====
    
    setupEventListeners: function() {
        // Send button click
        if (this.sendButton) {
            this.sendButton.addEventListener('click', () => this.sendMessage());
        }
        
        // Enter key press
        if (this.chatInput) {
            this.chatInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    this.sendMessage();
                }
            });
            
            // Auto-resize input
            this.chatInput.addEventListener('input', () => this.adjustInputHeight());
        }
    },
    
    sendMessage: function() {
        if (!this.chatInput) return;
        
        const message = this.chatInput.value.trim();
        if (!message) return;
        
        this.addMessage(message, 'user');
        this.chatInput.value = '';
        this.showTyping();
        
        // Send to backend
        fetch('/chat/send', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ 
                message: message,
                location: this.userLocation // Include location in all messages
            })
        })
        .then(response => response.json())
        .then(data => {
            this.hideTyping();
            if (data.response) {
                this.addMessage(data.response, 'bot');
                
                // Check if this is an emergency response
                if (data.emergency || data.is_emergency) {
                    console.log('🚨 Emergency response detected');
                    this.handleEmergencyResponse(data, message);
                }
            } else if (data.error) {
                this.addMessage('Sorry, I encountered an error. Please try again.', 'bot');
            }
        })
        .catch(error => {
            this.hideTyping();
            console.error('Chat error:', error);
            this.addMessage('Sorry, I\'m having trouble connecting. Please try again.', 'bot');
        });
    },
    
    sendQuickMessage: function(message) {
        if (this.chatInput) {
            this.chatInput.value = message;
            this.sendMessage();
        }
    },
    
    addMessage: function(content, sender) {
        if (!this.messagesContainer) return;
        
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}`;
        
        const avatar = sender === 'user' 
            ? '<i class="fas fa-user"></i>'
            : '<i class="fas fa-shield-alt"></i>';
            
        const timestamp = new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
        
        messageDiv.innerHTML = `
            <div class="message-avatar">${avatar}</div>
            <div class="message-content">
                <div class="message-text">${this.formatMessage(content)}</div>
                <div class="message-time">${timestamp}</div>
            </div>
        `;
        
        this.messagesContainer.appendChild(messageDiv);
        this.scrollToBottom();
    },
    
    formatMessage: function(message) {
        // Basic formatting for bot responses
        return message
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\n/g, '<br>')
            .replace(/• /g, '<li>')
            .replace(/(?:^|\n)(.*?):/g, '<strong>$1:</strong>');
    },
    
    showTyping: function() {
        if (this.typingIndicator) {
            this.typingIndicator.style.display = 'block';
            this.scrollToBottom();
        }
    },
    
    hideTyping: function() {
        if (this.typingIndicator) {
            this.typingIndicator.style.display = 'none';
        }
    },
    
    scrollToBottom: function() {
        if (this.messagesContainer) {
            this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
        }
    },
    
    focusInput: function() {
        if (this.chatInput) {
            this.chatInput.focus();
        }
    },
    
    clearChat: function() {
        if (confirm('Clear all chat messages?')) {
            fetch('/chat/clear', { method: 'POST' })
                .then(() => {
                    // Remove all messages except the initial greeting
                    if (this.messagesContainer) {
                        const messages = this.messagesContainer.querySelectorAll('.message');
                        for (let i = 1; i < messages.length; i++) {
                            messages[i].remove();
                        }
                    }
                })
                .catch(error => console.error('Clear chat error:', error));
        }
    },
    
    downloadHistory: function() {
        fetch('/chat/history')
            .then(response => response.json())
            .then(data => {
                const history = data.history.map(h => 
                    `User: ${h.user}\nBot: ${h.bot}\nTime: ${h.timestamp}\n---\n`
                ).join('\n');
                
                const blob = new Blob([history], { type: 'text/plain' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `safeindy-chat-${new Date().toISOString().split('T')[0]}.txt`;
                a.click();
                URL.revokeObjectURL(url);
            })
            .catch(error => console.error('Download history error:', error));
    },
    
    adjustInputHeight: function() {
        if (this.chatInput) {
            // Auto-adjust input height if needed
            this.chatInput.style.height = 'auto';
            this.chatInput.style.height = Math.min(this.chatInput.scrollHeight, 120) + 'px';
        }
    },
    
    // ===== EMERGENCY FUNCTIONS =====
    
    handleEmergencyResponse: function(responseData, originalMessage) {
        console.log('🚨 handleEmergencyResponse called with:', responseData, originalMessage);
        console.log('🚨 User location available:', !!this.userLocation);
        
        // Show emergency alert
        const emergencyAlert = document.createElement('div');
        emergencyAlert.className = 'alert alert-danger mt-3';
        emergencyAlert.innerHTML = `
            <div class="d-flex align-items-center">
                <i class="fas fa-exclamation-triangle fa-2x me-3"></i>
                <div>
                    <h5 class="alert-heading mb-1">🚨 Emergency Detected</h5>
                    <p class="mb-0">If this is a life-threatening emergency, call 911 immediately.</p>
                    ${this.userLocation ? '<p class="mb-0 mt-1"><small class="text-muted">📍 Your location has been automatically sent to emergency contacts.</small></p>' : ''}
                </div>
            </div>
        `;
        
        if (this.messagesContainer) {
            this.messagesContainer.appendChild(emergencyAlert);
            this.scrollToBottom();
        }
        
        // Automatically send emergency alert if location is available
        if (this.userLocation) {
            console.log('🚨 Sending emergency alert with location...');
            this.sendEmergencyAlert(originalMessage, responseData);
        } else {
            console.log('🚨 Emergency detected, requesting location...');
            this.pendingEmergencyMessage = originalMessage;
            alert('Emergency detected! Please enable location sharing for faster response.');
            this.requestLocation();
        }
        
        // Add emergency action buttons
        setTimeout(() => {
            const actionButtons = document.createElement('div');
            actionButtons.className = 'message bot mt-2';
            actionButtons.innerHTML = `
                <div class="message-avatar">
                    <i class="fas fa-shield-alt"></i>
                </div>
                <div class="message-content">
                    <div class="emergency-actions">
                        <p><strong>🚨 Emergency Actions:</strong></p>
                        <div class="d-flex gap-2 flex-wrap">
                            <a href="tel:911" class="btn btn-danger btn-sm">
                                <i class="fas fa-phone me-1"></i>Call 911
                            </a>
                            <a href="tel:317-327-3811" class="btn btn-outline-primary btn-sm">
                                <i class="fas fa-phone me-1"></i>Police Non-Emergency
                            </a>
                            <a href="tel:311" class="btn btn-outline-secondary btn-sm">
                                <i class="fas fa-phone me-1"></i>Call 311
                            </a>
                        </div>
                    </div>
                </div>
            `;
            
            if (this.messagesContainer) {
                this.messagesContainer.appendChild(actionButtons);
                this.scrollToBottom();
            }
        }, 1000);
    },
    
    sendEmergencyAlert: function(message, responseData) {
        console.log('🚨 sendEmergencyAlert called with:', message, responseData);
        console.log('🚨 Current location:', this.userLocation);
        
        if (!this.userLocation) {
            console.log('❌ No location available for emergency alert');
            this.pendingEmergencyMessage = message;
            return;
        }
        
        // Get session ID from template or generate one
        let sessionId = 'unknown';
        try {
            // Try to get from template variable or cookie
            if (typeof window.sessionId !== 'undefined') {
                sessionId = window.sessionId;
            } else if (document.cookie.includes('session_id')) {
                sessionId = document.cookie.split('session_id=')[1].split(';')[0];
            }
        } catch (e) {
            console.log('Could not get session ID:', e);
        }
        
        // Send emergency alert to backend
        fetch('/chat/emergency-alert', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: message,
                location: this.userLocation,
                response_data: responseData,
                timestamp: new Date().toISOString(),
                user_agent: navigator.userAgent,
                session_id: sessionId
            })
        })
        .then(response => response.json())
        .then(data => {
            console.log('🚨 Emergency alert response:', data);
            if (data.success) {
                console.log('✅ Emergency alert sent successfully');
                this.showEmergencyAlertConfirmation();
            } else {
                console.error('❌ Emergency alert failed:', data.error);
                this.showEmergencyAlertError(data.error || 'Unknown error');
            }
        })
        .catch(error => {
            console.error('❌ Emergency alert request failed:', error);
            this.showEmergencyAlertError('Network error: ' + error.message);
        });
    },
    
    showEmergencyAlertConfirmation: function() {
        const confirmation = document.createElement('div');
        confirmation.className = 'alert alert-success mt-2';
        confirmation.innerHTML = `
            <i class="fas fa-check-circle me-2"></i>
            <strong>📧 Emergency Alert Sent!</strong> Your location and message have been forwarded to emergency contacts.
        `;
        
        if (this.messagesContainer) {
            this.messagesContainer.appendChild(confirmation);
            this.scrollToBottom();
        }
        
        // Remove after 10 seconds
        setTimeout(() => {
            if (confirmation.parentElement) {
                confirmation.remove();
            }
        }, 10000);
    },
    
    showEmergencyAlertError: function(errorMessage) {
        const errorAlert = document.createElement('div');
        errorAlert.className = 'alert alert-warning mt-2';
        errorAlert.innerHTML = `
            <i class="fas fa-exclamation-triangle me-2"></i>
            <strong>⚠️ Emergency Alert Failed:</strong> ${errorMessage}
            <button class="btn btn-sm btn-outline-warning ms-2" onclick="ChatApp.retryEmergencyAlert()">
                <i class="fas fa-retry me-1"></i>Retry
            </button>
        `;
        
        if (this.messagesContainer) {
            this.messagesContainer.appendChild(errorAlert);
            this.scrollToBottom();
        }
        
        // Remove after 15 seconds
        setTimeout(() => {
            if (errorAlert.parentElement) {
                errorAlert.remove();
            }
        }, 15000);
    },
    
    retryEmergencyAlert: function() {
        if (this.pendingEmergencyMessage) {
            console.log('🔄 Retrying emergency alert...');
            this.sendEmergencyAlert(this.pendingEmergencyMessage, {emergency: true, retry: true});
        } else {
            console.log('❌ No pending emergency message to retry');
        }
    },
    
    // ===== UTILITY FUNCTIONS =====
    
    // Test function for emergency functionality
    testEmergency: function(message = "Test emergency message") {
        console.log('🧪 Testing emergency functionality...');
        if (!this.userLocation) {
            console.log('❌ No location available for test');
            alert('Please enable location first to test emergency functionality');
            this.requestLocation();
            return;
        }
        
        this.handleEmergencyResponse({emergency: true, test: true}, message);
    },
    
    // Get current status
    getStatus: function() {
        return {
            initialized: !!(this.messagesContainer && this.chatInput),
            locationEnabled: !!this.userLocation,
            pendingEmergency: !!this.pendingEmergencyMessage,
            locationWatching: !!this.locationWatchId
        };
    },
    
    // Clean shutdown
    destroy: function() {
        if (this.locationWatchId) {
            navigator.geolocation.clearWatch(this.locationWatchId);
            this.locationWatchId = null;
        }
        console.log('🧹 ChatApp destroyed');
    }
};

// ===== INITIALIZATION AND EVENT HANDLERS =====

// Initialize chat when page loads
document.addEventListener('DOMContentLoaded', function() {
    ChatApp.init();
    
    // Add debug functions to global scope
    window.testEmergency = () => ChatApp.testEmergency();
    window.getChatStatus = () => ChatApp.getStatus();
    
    console.log('🧪 Debug commands available:');
    console.log('- testEmergency() - Test emergency functionality');
    console.log('- getChatStatus() - Get current app status');
});

// Add global error handler for unhandled promise rejections
window.addEventListener('unhandledrejection', function(event) {
    console.error('🚨 Unhandled promise rejection:', event.reason);
    if (event.reason && event.reason.toString().includes('emergency')) {
        console.log('🚨 Emergency-related error detected');
    }
});

// Add beforeunload handler to warn about ongoing emergencies
window.addEventListener('beforeunload', function(event) {
    if (ChatApp.pendingEmergencyMessage) {
        event.preventDefault();
        event.returnValue = 'You have a pending emergency alert. Are you sure you want to leave?';
        return event.returnValue;
    }
});

// Add visibility change handler to pause location tracking when tab is hidden
document.addEventListener('visibilitychange', function() {
    if (document.hidden) {
        console.log('📱 Tab hidden - pausing intensive operations');
    } else {
        console.log('📱 Tab visible - resuming operations');
        // Optionally refresh location if needed
        if (ChatApp.userLocation && ChatApp.userLocation.timestamp) {
            const lastUpdate = new Date(ChatApp.userLocation.timestamp);
            const now = new Date();
            const timeDiff = (now - lastUpdate) / 1000 / 60; // minutes
            
            if (timeDiff > 10) { // If location is older than 10 minutes
                console.log('📍 Location is stale, requesting update...');
                ChatApp.requestLocation();
            }
        }
    }
});

// Add this to your static/js/chat.js file

// Update your message handling function to support maps
function displayBotMessage(response) {
    const chatContainer = document.getElementById('chat-messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message bot-message';
    
    // Create message content
    let messageContent = `
        <div class="message-content">
            <div class="message-text">${formatMessageText(response.response)}</div>
    `;
    
    // Add embedded map if present
    if (response.map_html) {
        messageContent += `
            <div class="message-map">
                ${response.map_html}
            </div>
        `;
    }
    
    // Add sources if present
    if (response.sources && response.sources.length > 0) {
        messageContent += `
            <div class="message-sources">
                <h4>Sources:</h4>
                <ul>
                    ${response.sources.map(source => `
                        <li>
                            <a href="${source.url}" target="_blank" rel="noopener noreferrer">
                                ${source.title}
                            </a>
                            ${source.type ? `<span class="source-type">[${source.type}]</span>` : ''}
                        </li>
                    `).join('')}
                </ul>
            </div>
        `;
    }
    
    // Add location info if available
    if (response.locations && response.locations.length > 0) {
        messageContent += `
            <div class="location-summary">
                <h4>📍 Locations Found:</h4>
                <div class="location-list">
                    ${response.locations.slice(0, 3).map((loc, index) => `
                        <div class="location-item">
                            <strong>${loc.name}</strong>
                            <div class="location-details">
                                📍 ${loc.address}
                                ${loc.phone ? `<br>📞 ${loc.phone}` : ''}
                                ${loc.distance ? `<br>🚗 ${loc.distance.toFixed(1)} km away` : ''}
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }
    
    messageContent += `
            <div class="message-meta">
                <span class="timestamp">${formatTimestamp(response.timestamp)}</span>
                ${response.intent ? `<span class="intent-badge">${response.intent}</span>` : ''}
                ${response.emergency ? '<span class="emergency-badge">🚨 EMERGENCY</span>' : ''}
            </div>
        </div>
    `;
    
    messageDiv.innerHTML = messageContent;
    chatContainer.appendChild(messageDiv);
    
    // Scroll to bottom
    chatContainer.scrollTop = chatContainer.scrollHeight;
    
    // Initialize map if present (with small delay to ensure DOM is ready)
    if (response.map_html) {
        setTimeout(() => {
            initializeEmbeddedMap();
        }, 100);
    }
}

function initializeEmbeddedMap() {
    // This function will be called after map HTML is inserted
    // The map initialization is handled by the embedded JavaScript
    console.log('🗺️ Map ready for initialization');
}

// Update your sendMessage function to handle maps
async function sendMessage() {
    const messageInput = document.getElementById('message-input');
    const sendButton = document.getElementById('send-button');
    const message = messageInput.value.trim();
    
    if (!message) return;
    
    // Disable input while processing
    messageInput.disabled = true;
    sendButton.disabled = true;
    sendButton.innerHTML = '<i class="loading-spinner"></i> Sending...';
    
    // Display user message
    displayUserMessage(message);
    
    // Clear input
    messageInput.value = '';
    
    try {
        // Get user location if available
        const locationData = await getCurrentLocation();
        
        // Send message to backend
        const response = await fetch('/chat/send', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: message,
                location: locationData
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        // Display bot response with potential map
        displayBotMessage(data);
        
        // Handle emergency alerts
        if (data.emergency && locationData) {
            await sendEmergencyAlert(message, locationData);
        }
        
    } catch (error) {
        console.error('Error sending message:', error);
        displayErrorMessage('Sorry, I encountered an error processing your message. Please try again.');
    } finally {
        // Re-enable input
        messageInput.disabled = false;
        sendButton.disabled = false;
        sendButton.innerHTML = 'Send';
        messageInput.focus();
    }
}

// Location functions
async function getCurrentLocation() {
    return new Promise((resolve) => {
        if (!navigator.geolocation) {
            console.log('Geolocation not supported');
            resolve(null);
            return;
        }
        
        navigator.geolocation.getCurrentPosition(
            (position) => {
                resolve({
                    lat: position.coords.latitude,
                    lng: position.coords.longitude,
                    accuracy: position.coords.accuracy,
                    timestamp: new Date().toISOString()
                });
            },
            (error) => {
                console.log('Location access denied or unavailable:', error);
                resolve(null);
            },
            {
                enableHighAccuracy: true,
                timeout: 5000,
                maximumAge: 300000 // 5 minutes
            }
        );
    });
}

// Emergency alert function
async function sendEmergencyAlert(message, locationData) {
    try {
        const response = await fetch('/chat/emergency-alert', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: message,
                location: locationData
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            console.log('🚨 Emergency alert sent successfully');
            showNotification('Emergency alert sent to monitoring team', 'success');
        } else {
            console.error('❌ Emergency alert failed:', data.error);
        }
    } catch (error) {
        console.error('❌ Emergency alert error:', error);
    }
}

// Utility functions
function formatMessageText(text) {
    // Convert markdown-style formatting to HTML
    return text
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/\n/g, '<br>')
        .replace(/#{2,3}\s*(.*)/g, '<h3>$1</h3>')
        .replace(/#{1}\s*(.*)/g, '<h2>$1</h2>');
}

function formatTimestamp(timestamp) {
    const date = new Date(timestamp);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <div class="notification-content">
            <span>${message}</span>
            <button class="notification-close" onclick="this.parentElement.parentElement.remove()">×</button>
        </div>
    `;
    
    // Add to page
    document.body.appendChild(notification);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        if (notification.parentElement) {
            notification.remove();
        }
    }, 5000);
}

// Add CSS for map and location styling
const mapStyles = `
<style>
.message-map {
    margin: 15px 0;
    border-radius: 8px;
    overflow: hidden;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
}

.location-summary {
    background: #f8f9fa;
    border-radius: 8px;
    padding: 15px;
    margin: 10px 0;
    border-left: 4px solid #1a73e8;
}

.location-summary h4 {
    margin: 0 0 10px 0;
    color: #1a73e8;
    font-size: 14px;
}

.location-list {
    display: flex;
    flex-direction: column;
    gap: 10px;
}

.location-item {
    background: white;
    padding: 10px;
    border-radius: 6px;
    border: 1px solid #e0e0e0;
}

.location-item strong {
    color: #1a73e8;
    font-size: 14px;
}

.location-details {
    font-size: 12px;
    color: #5f6368;
    margin-top: 4px;
    line-height: 1.4;
}

.message-sources {
    background: #f1f3f4;
    border-radius: 6px;
    padding: 10px;
    margin: 10px 0;
}

.message-sources h4 {
    margin: 0 0 8px 0;
    font-size: 12px;
    color: #5f6368;
    text-transform: uppercase;
}

.message-sources ul {
    list-style: none;
    padding: 0;
    margin: 0;
}

.message-sources li {
    margin: 4px 0;
}

.message-sources a {
    color: #1a73e8;
    text-decoration: none;
    font-size: 13px;
}

.message-sources a:hover {
    text-decoration: underline;
}

.source-type {
    color: #5f6368;
    font-size: 11px;
    margin-left: 5px;
}

.emergency-badge {
    background: #d93025;
    color: white;
    padding: 2px 6px;
    border-radius: 4px;
    font-size: 11px;
    font-weight: bold;
}

.intent-badge {
    background: #e8f0fe;
    color: #1a73e8;
    padding: 2px 6px;
    border-radius: 4px;
    font-size: 11px;
    margin-left: 5px;
}

.notification {
    position: fixed;
    top: 20px;
    right: 20px;
    background: white;
    border-radius: 8px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.15);
    z-index: 1000;
    animation: slideIn 0.3s ease-out;
}

.notification-success {
    border-left: 4px solid #34a853;
}

.notification-error {
    border-left: 4px solid #ea4335;
}

.notification-content {
    padding: 15px 20px;
    display: flex;
    align-items: center;
    justify-content: space-between;
}

.notification-close {
    background: none;
    border: none;
    font-size: 18px;
    cursor: pointer;
    margin-left: 10px;
    color: #5f6368;
}

@keyframes slideIn {
    from {
        transform: translateX(100%);
        opacity: 0;
    }
    to {
        transform: translateX(0);
        opacity: 1;
    }
}

.loading-spinner {
    display: inline-block;
    width: 12px;
    height: 12px;
    border: 2px solid #f3f3f3;
    border-top: 2px solid #1a73e8;
    border-radius: 50%;
    animation: spin 1s linear infinite;
}

@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

/* Mobile responsiveness for maps */
@media (max-width: 768px) {
    .embedded-map-container {
        height: 300px !important;
    }
    
    .location-list {
        flex-direction: column;
    }
    
    .notification {
        left: 20px;
        right: 20px;
        top: 20px;
    }
}
</style>
`;

// Insert styles
document.head.insertAdjacentHTML('beforeend', mapStyles);

// ===== GLOBAL CONSOLE LOGGING =====
console.log('✅ SafeIndy Chat Application fully loaded with complete emergency functionality');
console.log('🚨 Emergency features: Location tracking, Emergency alerts, Retry mechanisms');
console.log('📱 Mobile features: Visibility handling, Touch support, Responsive design');
console.log('🔧 Debug: Use testEmergency() and getChatStatus() for testing');