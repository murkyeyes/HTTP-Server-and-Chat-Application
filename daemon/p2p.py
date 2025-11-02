#
# Copyright (C) 2025 pdnguyen of HCMC University of Technology VNU-HCM.
# All rights reserved.
# This file is part of the CO3093/CO3094 course.
#
# WeApRous release
#
# The authors hereby grant to Licensee personal permission to use
# and modify the Licensed Source Code for the sole purpose of studying
# while attending the course
#

"""
daemon.p2p
~~~~~~~~~~~~~~~~~

This module implements peer-to-peer communication for the chat application.
It handles direct peer connections, message broadcasting, and P2P protocol.
"""

import socket
import threading
import json
import time
from datetime import datetime

class P2PNode:
    """
    A P2P node that can connect to other peers and exchange messages.
    """
    
    def __init__(self, peer_id, listen_port, tracker_host="localhost", tracker_port=8001):
        self.peer_id = peer_id
        self.listen_port = listen_port
        self.tracker_host = tracker_host
        self.tracker_port = tracker_port
        
        # P2P connections
        self.connections = {}  # {peer_id: socket}
        self.server_socket = None
        self.running = False
        
        # Message handling
        self.message_handlers = {}
        self.message_queue = []
        
        print("[P2P] Initialized node: {} on port {}".format(peer_id, listen_port))
    
    def start(self):
        """Start the P2P node - begin listening for connections."""
        self.running = True
        
        # Start listening for incoming connections
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            self.server_socket.bind(('0.0.0.0', self.listen_port))
            self.server_socket.listen(10)
            
            print("[P2P] Node {} listening on port {}".format(self.peer_id, self.listen_port))
            
            # Start accepting connections
            accept_thread = threading.Thread(target=self._accept_connections)
            accept_thread.daemon = True
            accept_thread.start()
            
            # Register with tracker
            self.register_with_tracker()
            
        except Exception as e:
            print("[P2P] Error starting node: {}".format(e))
            self.running = False
    
    def stop(self):
        """Stop the P2P node."""
        self.running = False
        
        # Close all connections
        for peer_id, conn in self.connections.items():
            try:
                conn.close()
            except:
                pass
        
        # Close server socket
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
        
        print("[P2P] Node {} stopped".format(self.peer_id))
    
    def _accept_connections(self):
        """Accept incoming P2P connections."""
        while self.running:
            try:
                conn, addr = self.server_socket.accept()
                print("[P2P] Incoming connection from {}".format(addr))
                
                # Handle connection in separate thread
                handler_thread = threading.Thread(
                    target=self._handle_connection,
                    args=(conn, addr)
                )
                handler_thread.daemon = True
                handler_thread.start()
                
            except Exception as e:
                if self.running:
                    print("[P2P] Error accepting connection: {}".format(e))
                break
    
    def _handle_connection(self, conn, addr):
        """Handle incoming P2P connection."""
        try:
            # Read handshake message
            data = conn.recv(1024).decode('utf-8')
            handshake = json.loads(data)
            
            if handshake.get('type') == 'handshake':
                remote_peer_id = handshake.get('peer_id')
                
                # Send handshake response
                response = {
                    'type': 'handshake_response',
                    'peer_id': self.peer_id,
                    'status': 'success'
                }
                conn.send(json.dumps(response).encode('utf-8'))
                
                # Store connection
                self.connections[remote_peer_id] = conn
                print("[P2P] Established connection with peer: {}".format(remote_peer_id))
                
                # Listen for messages from this peer
                self._listen_peer(conn, remote_peer_id)
            
        except Exception as e:
            print("[P2P] Error handling connection: {}".format(e))
        finally:
            conn.close()
    
    def _listen_peer(self, conn, peer_id):
        """Listen for messages from a connected peer."""
        while self.running:
            try:
                data = conn.recv(4096).decode('utf-8')
                if not data:
                    break
                
                message = json.loads(data)
                self._process_message(message, peer_id)
                
            except Exception as e:
                print("[P2P] Error listening to peer {}: {}".format(peer_id, e))
                break
        
        # Remove connection
        if peer_id in self.connections:
            del self.connections[peer_id]
        print("[P2P] Disconnected from peer: {}".format(peer_id))
    
    def _process_message(self, message, from_peer):
        """Process incoming message from peer."""
        msg_type = message.get('type', 'unknown')
        
        print("[P2P] Received {} from {}: {}".format(
            msg_type, from_peer, message.get('content', '')[:50]
        ))
        
        # Store message in queue
        message['from_peer'] = from_peer
        message['timestamp'] = datetime.now().isoformat()
        self.message_queue.append(message)
        
        # Call registered handlers
        if msg_type in self.message_handlers:
            try:
                self.message_handlers[msg_type](message, from_peer)
            except Exception as e:
                print("[P2P] Error in message handler: {}".format(e))
    
    def register_with_tracker(self):
        """Register this peer with the tracker server."""
        try:
            # Get local IP
            import socket as sock
            s = sock.socket(sock.AF_INET, sock.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            
            # Register with tracker using HTTP
            import urllib2
            import urllib
            
            data = {
                'peer_id': self.peer_id,
                'ip': local_ip,
                'port': self.listen_port
            }
            
            url = "http://{}:{}/submit-info".format(self.tracker_host, self.tracker_port)
            req_data = urllib.urlencode(data)
            
            request = urllib2.Request(url, req_data)
            request.add_header('Content-Type', 'application/x-www-form-urlencoded')
            
            response = urllib2.urlopen(request)
            result = response.read()
            
            print("[P2P] Registered with tracker: {}".format(result))
            
        except Exception as e:
            print("[P2P] Error registering with tracker: {}".format(e))
    
    def get_peers_from_tracker(self):
        """Get list of active peers from tracker."""
        try:
            import urllib2
            
            url = "http://{}:{}/get-list".format(self.tracker_host, self.tracker_port)
            response = urllib2.urlopen(url)
            result = json.loads(response.read())
            
            if result.get('status') == 'success':
                return result.get('peers', [])
            else:
                print("[P2P] Error getting peers: {}".format(result.get('message')))
                return []
                
        except Exception as e:
            print("[P2P] Error getting peers from tracker: {}".format(e))
            return []
    
    def connect_to_peer(self, peer_id, peer_ip, peer_port):
        """Connect to another peer."""
        if peer_id in self.connections:
            print("[P2P] Already connected to {}".format(peer_id))
            return True
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((peer_ip, int(peer_port)))
            
            # Send handshake
            handshake = {
                'type': 'handshake',
                'peer_id': self.peer_id
            }
            sock.send(json.dumps(handshake).encode('utf-8'))
            
            # Wait for response
            response_data = sock.recv(1024).decode('utf-8')
            response = json.loads(response_data)
            
            if response.get('status') == 'success':
                self.connections[peer_id] = sock
                print("[P2P] Connected to peer: {}".format(peer_id))
                
                # Start listening to this peer
                listen_thread = threading.Thread(
                    target=self._listen_peer,
                    args=(sock, peer_id)
                )
                listen_thread.daemon = True
                listen_thread.start()
                
                return True
            else:
                sock.close()
                return False
                
        except Exception as e:
            print("[P2P] Error connecting to peer {}: {}".format(peer_id, e))
            return False
    
    def send_message(self, peer_id, message_type, content):
        """Send message to specific peer."""
        if peer_id not in self.connections:
            print("[P2P] Not connected to peer: {}".format(peer_id))
            return False
        
        try:
            message = {
                'type': message_type,
                'content': content,
                'from': self.peer_id,
                'timestamp': datetime.now().isoformat()
            }
            
            data = json.dumps(message).encode('utf-8')
            self.connections[peer_id].send(data)
            
            print("[P2P] Sent {} to {}: {}".format(message_type, peer_id, content[:50]))
            return True
            
        except Exception as e:
            print("[P2P] Error sending message to {}: {}".format(peer_id, e))
            return False
    
    def broadcast_message(self, message_type, content):
        """Broadcast message to all connected peers."""
        sent_count = 0
        
        for peer_id in list(self.connections.keys()):
            if self.send_message(peer_id, message_type, content):
                sent_count += 1
        
        print("[P2P] Broadcasted {} to {} peers".format(message_type, sent_count))
        return sent_count
    
    def discover_and_connect_peers(self):
        """Discover peers from tracker and connect to them."""
        peers = self.get_peers_from_tracker()
        connected_count = 0
        
        for peer_info in peers:
            peer_id = peer_info['peer_id']
            
            # Don't connect to yourself
            if peer_id == self.peer_id:
                continue
            
            # Skip if already connected
            if peer_id in self.connections:
                continue
            
            peer_ip = peer_info['ip']
            peer_port = peer_info['port']
            
            if self.connect_to_peer(peer_id, peer_ip, peer_port):
                connected_count += 1
        
        print("[P2P] Connected to {} new peers".format(connected_count))
        return connected_count
    
    def register_message_handler(self, message_type, handler_func):
        """Register a handler function for specific message type."""
        self.message_handlers[message_type] = handler_func
        print("[P2P] Registered handler for: {}".format(message_type))
    
    def get_recent_messages(self, limit=50):
        """Get recent messages from the queue."""
        return self.message_queue[-limit:]
    
    def get_connected_peers(self):
        """Get list of currently connected peers."""
        return list(self.connections.keys())

# Example usage and chat handlers
def create_chat_handlers(p2p_node):
    """Create standard chat message handlers."""
    
    def handle_chat_message(message, from_peer):
        print("\n[CHAT] {}: {}".format(from_peer, message.get('content', '')))
    
    def handle_join_channel(message, from_peer):
        channel = message.get('channel', 'general')
        print("\n[CHAT] {} joined channel: {}".format(from_peer, channel))
    
    def handle_leave_channel(message, from_peer):
        channel = message.get('channel', 'general')
        print("\n[CHAT] {} left channel: {}".format(from_peer, channel))
    
    # Register handlers
    p2p_node.register_message_handler('chat_message', handle_chat_message)
    p2p_node.register_message_handler('join_channel', handle_join_channel)
    p2p_node.register_message_handler('leave_channel', handle_leave_channel)