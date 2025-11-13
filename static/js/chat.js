/**
 * WeApRous Chat Application JavaScript
 * Handles chat functionality, peer connections, and UI interactions
 * FIXED VERSION: Smart Merging of Pending Messages
 */

class ChatApp {
    constructor() {
        this.currentUser = null;
        this.currentChannel = 'general';
        this.peers = [];
        this.messages = [];
        this.isLoggedIn = false;
        
        // API endpoints - Tự động lấy IP hiện tại
        const baseUrl = window.location.protocol + "//" + window.location.host;
        this.apiBaseUrl = baseUrl;
        this.trackerUrl = baseUrl;
        
        this.init();
    }
    
    init() {
        this.bindEvents();
        this.updateConnectionStatus('disconnected');
        this.startPeriodicUpdates();
    }
    
    bindEvents() {

        document.getElementById('login-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleLogin();
        });
        

        document.getElementById('message-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleSendMessage();
        });
        

        document.getElementById('message-type').addEventListener('change', (e) => {
            this.handleMessageTypeChange(e.target.value);
        });
        

        document.getElementById('refresh-peers').addEventListener('click', () => {
            this.refreshPeers();
        });
        

        document.getElementById('connect-all-peers').addEventListener('click', () => {
            this.connectToAllPeers();
        });
        

        document.getElementById('clear-chat').addEventListener('click', () => {
            this.clearChat();
        });
        

        document.getElementById('logout-btn').addEventListener('click', () => {
            this.handleLogout();
        });
    }
    
    async handleLogin() {
        // Trim username để tránh lỗi so sánh sau này
        const username = document.getElementById('username').value.trim();
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
                
                await this.registerAsPeer();
                this.refreshPeers();
                this.getChannelMessages();
                
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
            const peerPort = Math.floor(Math.random() * 10000) + 50000;
            const currentIp = window.location.hostname;

            await this.makeRequest('POST', '/submit-info', {
                peer_id: this.currentUser,
                ip: currentIp, 
                port: peerPort
            });
            
            this.addSystemMessage('Registered as peer successfully');
        } catch (error) {
            console.error('Peer registration error:', error);
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
        }
    }
    
    updatePeerList() {
        const peerList = document.getElementById('peer-list');
        const peerCount = document.getElementById('peer-count');
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
        const currentSelection = select.value;
        select.innerHTML = '<option value="">Select Peer...</option>';
        
        const otherPeers = this.peers.filter(peer => peer.peer_id !== this.currentUser);
        otherPeers.forEach(peer => {
            const option = document.createElement('option');
            option.value = peer.peer_id;
            option.textContent = peer.peer_id;
            if (peer.peer_id === currentSelection) option.selected = true;
            select.appendChild(option);
        });
    }
    
    selectPeerForDirectMessage(peerId) {
        document.getElementById('message-type').value = 'direct';
        this.handleMessageTypeChange('direct');
        const select = document.getElementById('target-peer');
        if (!select.querySelector(`option[value="${peerId}"]`)) {
             const option = document.createElement('option');
             option.value = peerId;
             option.textContent = peerId;
             select.appendChild(option);
        }
        select.value = peerId;
        document.getElementById('message-input').focus();
    }
    
    handleMessageTypeChange(type) {
        const targetPeerSelect = document.getElementById('target-peer');
        targetPeerSelect.style.display = (type === 'direct') ? 'block' : 'none';
    }
    
    async handleSendMessage() {
        const messageInput = document.getElementById('message-input');
        const messageType = document.getElementById('message-type').value;
        const targetPeer = document.getElementById('target-peer').value;
        const message = messageInput.value.trim();
        
        if (!message) return;
        
        try {
            // 1. Hiển thị ngay lập tức (Pending)
            this.addMessage(this.currentUser, message, 'own', null, true);
            messageInput.value = '';

            let response;
            if (messageType === 'broadcast') {
                response = await this.makeRequest('POST', '/broadcast-peer', {
                    from_peer: this.currentUser,
                    message: message,
                    channel: this.currentChannel
                });

            } else if (messageType === 'direct' && targetPeer) {

                response = await this.makeRequest('POST', '/send-peer', {
                    from_peer: this.currentUser,
                    to_peer: targetPeer,
                    message: message
                });
                // Với tin nhắn direct, chúng ta cập nhật thêm text hiển thị
                // Lưu ý: Logic merge có thể phức tạp hơn với direct, nhưng cơ bản vẫn hoạt động
            }
            
            if (response && response.status === 'success') {

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
                if (response.status === 'success') connectedCount++;
            } catch (error) { console.error(error); }
        }
        this.addSystemMessage(`Connected to ${connectedCount} out of ${otherPeers.length} peers`);
    }
    
    // --- HÀM QUAN TRỌNG NHẤT ĐỂ FIX LỖI ---
    addMessage(sender, content, type = 'other', serverTimestamp = null, isPending = false) {
        // Chuẩn hóa dữ liệu để so sánh chính xác
        const cleanSender = sender ? sender.trim() : 'Unknown';
        const cleanContent = content ? content.trim() : '';

        // 1. Nếu tin này đã có Timestamp từ server (tức là tin thật), kiểm tra xem nó đã tồn tại chưa
        if (serverTimestamp) {
            const alreadyExists = this.messages.some(m => m.timestamp === serverTimestamp);
            if (alreadyExists) return; // Đã có rồi thì thôi, không làm gì cả
        }

        // 2. Logic "Hợp nhất" (Merge): 
        // Nếu đây là tin từ Server (có timestamp) VÀ không phải Pending
        if (serverTimestamp && !isPending) {
            // Tìm xem trong danh sách hiện tại có tin Pending nào khớp không (Cùng người gửi, Cùng nội dung)
            const pendingIdx = this.messages.findIndex(m => 
                m.isPending && 
                m.sender === cleanSender && 
                m.content === cleanContent
            );

            if (pendingIdx !== -1) {
                // -> TÌM THẤY! Đây chính là tin mình vừa gửi.
                const pendingMsg = this.messages[pendingIdx];
                
                // Cập nhật thông tin cho nó thành tin chính thức
                pendingMsg.timestamp = serverTimestamp;
                pendingMsg.isPending = false;
                
                // Cập nhật giao diện HTML tương ứng
                if (pendingMsg.element) {
                    pendingMsg.element.classList.remove('msg-pending'); // Bỏ hiệu ứng mờ nếu có
                    const timeDiv = pendingMsg.element.querySelector('.message-time');
                    if (timeDiv) {
                        timeDiv.textContent = new Date(serverTimestamp).toLocaleTimeString();
                    }
                }
                // Kết thúc hàm, không tạo bong bóng chat mới -> KHẮC PHỤC LỖI NHÂN ĐÔI
                return; 
            }
        }

        // 3. Nếu chạy đến đây, tức là:
        // - Hoặc là tin Pending mới tinh (vừa bấm gửi)
        // - Hoặc là tin từ Server mà chưa có trong danh sách Pending (tin người khác gửi, hoặc tin cũ)
        
        const messageContainer = document.getElementById('message-container');
        const messageElement = document.createElement('div');
        messageElement.className = `message ${type}`;
        if (isPending) messageElement.classList.add('msg-pending'); // Thêm class để đánh dấu

        const displayTime = serverTimestamp ? new Date(serverTimestamp).toLocaleTimeString() : new Date().toLocaleTimeString();
        
        messageElement.innerHTML = `
            <div class="message-header">${this.escapeHtml(cleanSender)}</div>
            <div class="message-content">${this.escapeHtml(cleanContent)}</div>
            <div class="message-time">${displayTime}</div>
        `;
        
        messageContainer.appendChild(messageElement);
        messageContainer.scrollTop = messageContainer.scrollHeight;
        
        // Lưu vào bộ nhớ để quản lý
        this.messages.push({
            sender: cleanSender,
            content: cleanContent,
            timestamp: serverTimestamp,
            type: type,
            isPending: isPending,
            element: messageElement
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
            const response = await this.makeRequest('GET', `/get-messages?channel=${this.currentChannel}`);
            
            if (response.status === 'success' && response.messages) {
                response.messages.forEach(msg => {
                    const type = msg.from === this.currentUser ? 'own' : 'other';
                    // Gọi thẳng addMessage, để nó tự xử lý việc hợp nhất (merge)
                    this.addMessage(msg.from, msg.message, type, msg.timestamp, false);
                });
            }
        } catch (error) { }
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
        const err = document.getElementById('login-error');
        if(err) err.textContent = '';
    }
    
    updateConnectionStatus(status) {
        const statusElement = document.getElementById('connection-status');
        if(statusElement) {
            statusElement.textContent = status.charAt(0).toUpperCase() + status.slice(1);
            statusElement.className = status;
        }
    }
    
    updateMessageStatus(message) {
        const statusElement = document.getElementById('message-status');
        if(!statusElement) return;
        statusElement.textContent = message;
        setTimeout(() => { statusElement.textContent = ''; }, 3000);
    }
    
    showError(elementId, message) {
        const errorElement = document.getElementById(elementId);
        if(errorElement) {
            errorElement.textContent = message;
            setTimeout(() => { errorElement.textContent = ''; }, 5000);
        }
    }
    
    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    async makeRequest(method, endpoint, data = null) {
        const url = this.trackerUrl + endpoint;
        const options = {
            method: method,
            headers: { 'Content-Type': 'application/json' }
        };
        if (data && method !== 'GET') options.body = JSON.stringify(data);
        const response = await fetch(url, options);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return await response.json();
    }
    
    startPeriodicUpdates() {

        setInterval(() => {
            if (this.isLoggedIn) 
            {
                this.getChannelMessages();
                this.refreshPeers();
            }
        }, 2000);
    }
}


document.addEventListener('DOMContentLoaded', () => {
    window.chatApp = new ChatApp();
});