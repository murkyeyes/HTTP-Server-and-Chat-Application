/**
 * WeApRous Chat Application JavaScript
 * Handles chat functionality, peer connections, and UI interactions
 */

class ChatApp {
    constructor() {
        this.currentUser = null;
        this.currentChannel = 'general';
        this.peers = [];
        this.messages = [];
        this.isLoggedIn = false;
        
        // API endpoints
        this.apiBaseUrl = 'http://localhost:8001';
        this.trackerUrl = 'http://localhost:8001';
        
        this.init();
    }
    
    init() {
        this.bindEvents();
        this.updateConnectionStatus('disconnected');
        this.startPeriodicUpdates();
    }
    
    bindEvents() {
        // Login form
        document.getElementById('login-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleLogin();
        });
        
        // Message form
        document.getElementById('message-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleSendMessage();
        });
        
        // Message type change
        document.getElementById('message-type').addEventListener('change', (e) => {
            this.handleMessageTypeChange(e.target.value);
        });
        
        // Refresh peers button
        document.getElementById('refresh-peers').addEventListener('click', () => {
            this.refreshPeers();
        });
        
        // Connect all peers button
        document.getElementById('connect-all-peers').addEventListener('click', () => {
            this.connectToAllPeers();
        });
        
        // Clear chat button
        document.getElementById('clear-chat').addEventListener('click', () => {
            this.clearChat();
        });
        
        // Logout button
        document.getElementById('logout-btn').addEventListener('click', () => {
            this.handleLogout();
        });
    }
    
    async handleLogin() {
        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;
        
        try {
            const response = await this.makeRequest('POST', '/login', {
                username: username,
                password: password
            });
            
            if (response.status === 'success') {
                this.currentUser = username;
                this.isLoggedIn = true;
                this.showChatSection();
                this.updateConnectionStatus('connected');
                this.addSystemMessage(`Welcome ${username}! You are now logged in.`);
                
                // Register as peer
                await this.registerAsPeer();
                
                // Start refreshing peers
                this.refreshPeers();
                
            } else {
                this.showError('login-error', response.message || 'Login failed');
            }
        } catch (error) {
            console.error('Login error:', error);
            this.showError('login-error', 'Network error. Please try again.');
        }
    }
    
    async registerAsPeer() {
        try {
            // Generate a random port for P2P communication
            const peerPort = Math.floor(Math.random() * 10000) + 50000;
            
            const response = await this.makeRequest('POST', '/submit-info', {
                peer_id: this.currentUser,
                ip: '127.0.0.1', // localhost for demo
                port: peerPort
            });
            
            if (response.status === 'success') {
                this.addSystemMessage('Registered as peer successfully');
            }
        } catch (error) {
            console.error('Peer registration error:', error);
            this.addSystemMessage('Failed to register as peer');
        }
    }
    
    async refreshPeers() {
        try {
            const response = await this.makeRequest('GET', '/get-list');
            
            if (response.status === 'success') {
                this.peers = response.peers || [];
                this.updatePeerList();
                this.updateTargetPeerSelect();
            }
        } catch (error) {
            console.error('Refresh peers error:', error);
            this.addSystemMessage('Failed to refresh peers');
        }
    }
    
    updatePeerList() {
        const peerList = document.getElementById('peer-list');
        const peerCount = document.getElementById('peer-count');
        
        // Filter out current user
        const otherPeers = this.peers.filter(peer => peer.peer_id !== this.currentUser);
        
        peerList.innerHTML = '';
        
        otherPeers.forEach(peer => {
            const li = document.createElement('li');
            li.className = 'peer';
            li.innerHTML = `
                <div class="peer-status"></div>
                <span>${peer.peer_id}</span>
                <small>(${peer.ip}:${peer.port})</small>
            `;
            
            li.addEventListener('click', () => {
                this.selectPeerForDirectMessage(peer.peer_id);
            });
            
            peerList.appendChild(li);
        });
        
        peerCount.textContent = otherPeers.length;
    }
    
    updateTargetPeerSelect() {
        const select = document.getElementById('target-peer');
        select.innerHTML = '<option value="">Select Peer...</option>';
        
        const otherPeers = this.peers.filter(peer => peer.peer_id !== this.currentUser);
        
        otherPeers.forEach(peer => {
            const option = document.createElement('option');
            option.value = peer.peer_id;
            option.textContent = peer.peer_id;
            select.appendChild(option);
        });
    }
    
    selectPeerForDirectMessage(peerId) {
        document.getElementById('message-type').value = 'direct';
        document.getElementById('target-peer').value = peerId;
        document.getElementById('target-peer').style.display = 'block';
        document.getElementById('message-input').focus();
    }
    
    handleMessageTypeChange(type) {
        const targetPeerSelect = document.getElementById('target-peer');
        
        if (type === 'direct') {
            targetPeerSelect.style.display = 'block';
        } else {
            targetPeerSelect.style.display = 'none';
        }
    }
    
    async handleSendMessage() {
        const messageInput = document.getElementById('message-input');
        const messageType = document.getElementById('message-type').value;
        const targetPeer = document.getElementById('target-peer').value;
        const message = messageInput.value.trim();
        
        if (!message) return;
        
        try {
            let response;
            
            if (messageType === 'broadcast') {
                response = await this.makeRequest('POST', '/broadcast-peer', {
                    from_peer: this.currentUser,
                    message: message,
                    channel: this.currentChannel
                });
                
                // Add message to local display
                this.addMessage(this.currentUser, message, 'own');
                
            } else if (messageType === 'direct' && targetPeer) {
                response = await this.makeRequest('POST', '/send-peer', {
                    from_peer: this.currentUser,
                    to_peer: targetPeer,
                    message: message
                });
                
                // Add message to local display
                this.addMessage(this.currentUser, `[To ${targetPeer}] ${message}`, 'own');
            }
            
            if (response && response.status === 'success') {
                messageInput.value = '';
                this.updateMessageStatus('Message sent');
            } else {
                this.updateMessageStatus('Failed to send message');
            }
            
        } catch (error) {
            console.error('Send message error:', error);
            this.updateMessageStatus('Network error');
        }
    }
    
    async connectToAllPeers() {
        const otherPeers = this.peers.filter(peer => peer.peer_id !== this.currentUser);
        let connectedCount = 0;
        
        for (const peer of otherPeers) {
            try {
                const response = await this.makeRequest('POST', '/connect-peer', {
                    from_peer: this.currentUser,
                    to_peer: peer.peer_id
                });
                
                if (response.status === 'success') {
                    connectedCount++;
                }
            } catch (error) {
                console.error(`Failed to connect to ${peer.peer_id}:`, error);
            }
        }
        
        this.addSystemMessage(`Connected to ${connectedCount} out of ${otherPeers.length} peers`);
    }
    
    addMessage(sender, content, type = 'other', serverTimestamp = null) {
        const messageContainer = document.getElementById('message-container');
        const messageElement = document.createElement('div');
        messageElement.className = `message ${type}`;
        
        // SỬA LỖI: Ưu tiên timestamp của server nếu có, nếu không thì dùng thời gian hiện tại
        const displayTime = serverTimestamp ? new Date(serverTimestamp).toLocaleTimeString() : new Date().toLocaleTimeString();
        const storedTimestamp = serverTimestamp ? serverTimestamp : new Date().toISOString();

        messageElement.innerHTML = `
            <div class="message-header">${sender}</div>
            <div class="message-content">${this.escapeHtml(content)}</div>
            <div class="message-time">${displayTime}</div>
        `;
        
        messageContainer.appendChild(messageElement);
        messageContainer.scrollTop = messageContainer.scrollHeight;
        
        // Store message
        this.messages.push({
            sender: sender,
            content: content,
            timestamp: storedTimestamp, // <-- SỬA LỖI: Lưu timestamp chính xác
            type: type
        });
    }
    
    addSystemMessage(content) {
        const messageContainer = document.getElementById('message-container');
        const messageElement = document.createElement('div');
        messageElement.className = 'message system';
        
        const timestamp = new Date().toLocaleTimeString();
        
        messageElement.innerHTML = `
            <div class="message-content">${this.escapeHtml(content)}</div>
            <div class="message-time">${timestamp}</div>
        `;
        
        messageContainer.appendChild(messageElement);
        messageContainer.scrollTop = messageContainer.scrollHeight;
    }
    
    clearChat() {
        document.getElementById('message-container').innerHTML = '';
        this.messages = [];
        this.addSystemMessage('Chat cleared');
    }
    
    async getChannelMessages() {
        try {
            // Sửa lỗi: Chỉ lấy tin nhắn cho kênh hiện tại
            const response = await this.makeRequest('GET', `/get-messages?channel=${this.currentChannel}`);
            
            if (response.status === 'success' && response.messages) {
                response.messages.forEach(msg => {
                    // SỬA LỖI: Kiểm tra xem tin nhắn đã tồn tại hay chưa
                    const messageExists = this.messages.some(m => 
                        m.timestamp === msg.timestamp && m.sender === msg.from
                    );

                    // Chỉ thêm tin nhắn nếu nó là của người khác VÀ nó chưa tồn tại
                    if (msg.from !== this.currentUser && !messageExists) {
                        this.addMessage(msg.from, msg.message, 'other', msg.timestamp);
                    }
                });
            }
        } catch (error) {
            console.error('Get messages error:', error);
        }
    }   
    
    showChatSection() {
        document.getElementById('login-section').style.display = 'none';
        document.getElementById('chat-section').style.display = 'flex';
        document.getElementById('current-user').textContent = this.currentUser;
        document.getElementById('logout-btn').style.display = 'block';
    }
    
    showLoginSection() {
        document.getElementById('login-section').style.display = 'flex';
        document.getElementById('chat-section').style.display = 'none';
        document.getElementById('logout-btn').style.display = 'none';
    }
    
    handleLogout() {
        this.isLoggedIn = false;
        this.currentUser = null;
        this.peers = [];
        this.messages = [];
        
        this.showLoginSection();
        this.updateConnectionStatus('disconnected');
        this.clearForm();
    }
    
    clearForm() {
        document.getElementById('username').value = '';
        document.getElementById('password').value = '';
        document.getElementById('message-input').value = '';
        document.getElementById('login-error').textContent = '';
    }
    
    updateConnectionStatus(status) {
        const statusElement = document.getElementById('connection-status');
        statusElement.textContent = status.charAt(0).toUpperCase() + status.slice(1);
        statusElement.className = status;
    }
    
    updateMessageStatus(message) {
        const statusElement = document.getElementById('message-status');
        statusElement.textContent = message;
        
        // Clear after 3 seconds
        setTimeout(() => {
            statusElement.textContent = '';
        }, 3000);
    }
    
    showError(elementId, message) {
        const errorElement = document.getElementById(elementId);
        errorElement.textContent = message;
        
        // Clear after 5 seconds
        setTimeout(() => {
            errorElement.textContent = '';
        }, 5000);
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    async makeRequest(method, endpoint, data = null) {
        const url = this.trackerUrl + endpoint;
        const options = {
            method: method,
            headers: {
                'Content-Type': 'application/json',
            }
        };
        
        if (data && method !== 'GET') {
            options.body = JSON.stringify(data);
        }
        
        const response = await fetch(url, options);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        return await response.json();
    }
    
    startPeriodicUpdates() {
        // Refresh peers every 30 seconds if logged in
        setInterval(() => {
            if (this.isLoggedIn) {
                this.refreshPeers();
                this.getChannelMessages();
            }
        }, 30000);
        
        // Update message status every 10 seconds if logged in
        setInterval(() => {
            if (this.isLoggedIn) {
                this.updateMessageStatus('');
            }
        }, 10000);
    }
}

// Initialize the chat application when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.chatApp = new ChatApp();
});