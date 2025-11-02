#
# Copyright (C) 2025 pdnguyen of HCMC University of Technology VNU-HCM.
# All rights reserved.
# This file is part of the CO3093/CO3094 course,
# and is released under the "MIT License Agreement". Please see the LICENSE
# file that should have been included as part of this package.
#
# WeApRous release
#
# The authors hereby grant to Licensee personal permission to use
# and modify the Licensed Source Code for the sole purpose of studying
# while attending the course
#

"""
start_chatapp
~~~~~~~~~~~~~~~~~

This module provides a chat application using the WeApRous framework.
It implements a hybrid chat system with both client-server (for peer discovery)
and peer-to-peer (for direct messaging) paradigms.
"""

import json
import socket
import argparse
import threading
import time
from datetime import datetime

from daemon.weaprous import WeApRous

PORT = 8001  # Default port for chat server

# Global data structures for chat application
active_peers = {}  # {peer_id: {"ip": ip, "port": port, "last_seen": timestamp}}
channels = {}      # {channel_id: {"members": [peer_ids], "messages": []}}
peer_connections = {}  # {peer_id: socket_connection}

app = WeApRous()

@app.route('/login', methods=['POST'])
def chat_login(headers="guest", body="anonymous"):
    """
    Handle user login for chat application.
    Expected body: {"username": "user1", "password": "pass"}
    """
    try:
        data = json.loads(body) if body else {}
        username = data.get('username', 'anonymous')
        password = data.get('password', '')
        
        print("[ChatApp] Login attempt: {}".format(username))
        
        # Simple authentication (can be enhanced)
        if username and password:
            response = {
                "status": "success",
                "message": "Login successful",
                "user_id": username,
                "timestamp": datetime.now().isoformat()
            }
        else:
            response = {
                "status": "error", 
                "message": "Invalid credentials"
            }
            
        return json.dumps(response)
    except Exception as e:
        print("[ChatApp] Login error: {}".format(e))
        return json.dumps({"status": "error", "message": "Login failed"})

@app.route('/submit-info', methods=['POST'])
def submit_peer_info(headers="guest", body="anonymous"):
    """
    Register peer information with the tracker server.
    Expected body: {"peer_id": "user1", "ip": "192.168.1.100", "port": 9999}
    """
    try:
        data = json.loads(body) if body else {}
        peer_id = data.get('peer_id')
        peer_ip = data.get('ip')
        peer_port = data.get('port')
        
        if peer_id and peer_ip and peer_port:
            active_peers[peer_id] = {
                "ip": peer_ip,
                "port": peer_port,
                "last_seen": time.time()
            }
            
            print("[ChatApp] Peer registered: {} at {}:{}".format(peer_id, peer_ip, peer_port))
            
            response = {
                "status": "success",
                "message": "Peer registered successfully",
                "peer_id": peer_id
            }
        else:
            response = {
                "status": "error",
                "message": "Missing peer information"
            }
            
        return json.dumps(response)
    except Exception as e:
        print("[ChatApp] Submit info error: {}".format(e))
        return json.dumps({"status": "error", "message": "Registration failed"})

@app.route('/get-list', methods=['GET'])
def get_peer_list(headers="guest", body="anonymous"):
    """
    Get list of active peers for peer discovery.
    Returns: {"peers": [{"peer_id": "user1", "ip": "192.168.1.100", "port": 9999}]}
    """
    try:
        # Clean up old peers (remove peers not seen for 5 minutes)
        current_time = time.time()
        expired_peers = [
            peer_id for peer_id, info in active_peers.items()
            if current_time - info['last_seen'] > 300
        ]
        for peer_id in expired_peers:
            del active_peers[peer_id]
            print("[ChatApp] Removed expired peer: {}".format(peer_id))
        
        peers_list = []
        for peer_id, info in active_peers.items():
            peers_list.append({
                "peer_id": peer_id,
                "ip": info['ip'],
                "port": info['port']
            })
        
        response = {
            "status": "success",
            "peers": peers_list,
            "count": len(peers_list)
        }
        
        print("[ChatApp] Returned peer list: {} peers".format(len(peers_list)))
        return json.dumps(response)
    except Exception as e:
        print("[ChatApp] Get list error: {}".format(e))
        return json.dumps({"status": "error", "message": "Failed to get peer list"})

@app.route('/connect-peer', methods=['POST'])
def connect_peer(headers="guest", body="anonymous"):
    """
    Initiate P2P connection to another peer.
    Expected body: {"from_peer": "user1", "to_peer": "user2"}
    """
    try:
        data = json.loads(body) if body else {}
        from_peer = data.get('from_peer')
        to_peer = data.get('to_peer')
        
        if from_peer and to_peer and to_peer in active_peers:
            target_info = active_peers[to_peer]
            
            response = {
                "status": "success",
                "target_peer": {
                    "peer_id": to_peer,
                    "ip": target_info['ip'],
                    "port": target_info['port']
                }
            }
            
            print("[ChatApp] Connection info provided: {} -> {}".format(from_peer, to_peer))
        else:
            response = {
                "status": "error",
                "message": "Peer not found or offline"
            }
            
        return json.dumps(response)
    except Exception as e:
        print("[ChatApp] Connect peer error: {}".format(e))
        return json.dumps({"status": "error", "message": "Connection failed"})

@app.route('/broadcast-peer', methods=['POST'])
def broadcast_peer(headers="guest", body="anonymous"):
    """
    Broadcast message to all active peers.
    Expected body: {"from_peer": "user1", "message": "Hello everyone!", "channel": "general"}
    """
    try:
        data = json.loads(body) if body else {}
        from_peer = data.get('from_peer')
        message = data.get('message')
        channel = data.get('channel', 'general')
        
        if from_peer and message:
            # Store message in channel
            if channel not in channels:
                channels[channel] = {"members": [], "messages": []}
            
            message_data = {
                "from": from_peer,
                "message": message,
                "timestamp": datetime.now().isoformat(),
                "channel": channel
            }
            
            channels[channel]["messages"].append(message_data)
            
            # Add sender to channel members if not already
            if from_peer not in channels[channel]["members"]:
                channels[channel]["members"].append(from_peer)
            
            print("[ChatApp] Broadcast message from {} in channel {}: {}".format(from_peer, channel, message))
            
            response = {
                "status": "success",
                "message": "Message broadcasted",
                "recipients": len(active_peers) - 1  # Exclude sender
            }
        else:
            response = {
                "status": "error",
                "message": "Missing message data"
            }
            
        return json.dumps(response)
    except Exception as e:
        print("[ChatApp] Broadcast error: {}".format(e))
        return json.dumps({"status": "error", "message": "Broadcast failed"})

@app.route('/send-peer', methods=['POST'])
def send_peer(headers="guest", body="anonymous"):
    """
    Send direct message to specific peer.
    Expected body: {"from_peer": "user1", "to_peer": "user2", "message": "Hello!"}
    """
    try:
        data = json.loads(body) if body else {}
        from_peer = data.get('from_peer')
        to_peer = data.get('to_peer')
        message = data.get('message')
        
        if from_peer and to_peer and message and to_peer in active_peers:
            # Store private message (optional)
            message_data = {
                "from": from_peer,
                "to": to_peer,
                "message": message,
                "timestamp": datetime.now().isoformat(),
                "type": "private"
            }
            
            print("[ChatApp] Direct message from {} to {}: {}".format(from_peer, to_peer, message))
            
            response = {
                "status": "success",
                "message": "Message sent to {}".format(to_peer),
                "target_peer": active_peers[to_peer]
            }
        else:
            response = {
                "status": "error",
                "message": "Invalid message or peer not found"
            }
            
        return json.dumps(response)
    except Exception as e:
        print("[ChatApp] Send peer error: {}".format(e))
        return json.dumps({"status": "error", "message": "Send failed"})

@app.route('/get-messages', methods=['GET'])
def get_messages(headers="guest", body="anonymous"):
    """
    Get messages from a specific channel.
    Expected query: ?channel=general&limit=50
    """
    try:
        # Parse query parameters (simplified)
        channel = "general"  # Default channel
        limit = 50          # Default limit
        
        if channel in channels:
            messages = channels[channel]["messages"][-limit:]  # Get last N messages
            
            response = {
                "status": "success",
                "channel": channel,
                "messages": messages,
                "count": len(messages)
            }
        else:
            response = {
                "status": "success",
                "channel": channel,
                "messages": [],
                "count": 0
            }
        
        return json.dumps(response)
    except Exception as e:
        print("[ChatApp] Get messages error: {}".format(e))
        return json.dumps({"status": "error", "message": "Failed to get messages"})

@app.route('/channels', methods=['GET'])
def get_channels(headers="guest", body="anonymous"):
    """
    Get list of available channels.
    """
    try:
        channel_list = []
        for channel_id, channel_info in channels.items():
            channel_list.append({
                "channel_id": channel_id,
                "members": len(channel_info["members"]),
                "messages": len(channel_info["messages"])
            })
        
        response = {
            "status": "success",
            "channels": channel_list,
            "count": len(channel_list)
        }
        
        return json.dumps(response)
    except Exception as e:
        print("[ChatApp] Get channels error: {}".format(e))
        return json.dumps({"status": "error", "message": "Failed to get channels"})

def cleanup_peers():
    """Background task to clean up inactive peers."""
    while True:
        try:
            current_time = time.time()
            expired_peers = [
                peer_id for peer_id, info in active_peers.items()
                if current_time - info['last_seen'] > 300  # 5 minutes timeout
            ]
            
            for peer_id in expired_peers:
                del active_peers[peer_id]
                print("[ChatApp] Cleaned up expired peer: {}".format(peer_id))
            
            time.sleep(60)  # Check every minute
        except Exception as e:
            print("[ChatApp] Cleanup error: {}".format(e))
            time.sleep(60)

if __name__ == "__main__":
    # Parse command-line arguments to configure server IP and port
    parser = argparse.ArgumentParser(prog='ChatApp', description='Chat Application Server', epilog='WeApRous Chat daemon')
    parser.add_argument('--server-ip', default='0.0.0.0')
    parser.add_argument('--server-port', type=int, default=PORT)
 
    args = parser.parse_args()
    ip = args.server_ip
    port = args.server_port

    # Start background cleanup task
    cleanup_thread = threading.Thread(target=cleanup_peers)
    cleanup_thread.daemon = True
    cleanup_thread.start()

    print("[ChatApp] Starting chat application server on {}:{}".format(ip, port))
    print("[ChatApp] Available endpoints:")
    print("  POST /login - User authentication")
    print("  POST /submit-info - Register peer")
    print("  GET  /get-list - Get active peers")
    print("  POST /connect-peer - Get peer connection info")
    print("  POST /broadcast-peer - Broadcast message")
    print("  POST /send-peer - Send direct message")
    print("  GET  /get-messages - Get channel messages")
    print("  GET  /channels - Get available channels")

    # Prepare and launch the chat application
    app.prepare_address(ip, port)
    app.run()