#
# Copyright (C) 2025 pdnguyen of HCMC University of Technology VNU-HCM.
# All rights reserved.
# This file is part of the CO3093/CO3094 course.
#

"""
p2p_client
~~~~~~~~~~~~~~~~~

Example P2P client for the chat application.
Demonstrates how to use the P2P communication layer.
"""

import sys
import time
import threading
import argparse
from daemon.p2p import P2PNode, create_chat_handlers

# Thêm vào sau các dòng import
try:
    input = raw_input
except NameError:
    pass

def main():
    parser = argparse.ArgumentParser(description='P2P Chat Client')
    parser.add_argument('--peer-id', required=True, help='Your peer ID')
    parser.add_argument('--port', type=int, required=True, help='Port to listen on')
    parser.add_argument('--tracker-host', default='localhost', help='Tracker server host')
    parser.add_argument('--tracker-port', type=int, default=8001, help='Tracker server port')
    
    args = parser.parse_args()
    
    # Create P2P node
    node = P2PNode(
        peer_id=args.peer_id,
        listen_port=args.port,
        tracker_host=args.tracker_host,
        tracker_port=args.tracker_port
    )
    
    # Setup chat handlers
    create_chat_handlers(node)
    
    # Start the node
    node.start()
    
    print("\\n=== P2P Chat Client ===")
    print("Peer ID: {}".format(args.peer_id))
    print("Commands:")
    print("  /discover - Discover and connect to peers")
    print("  /peers - Show connected peers")
    print("  /connect <peer_id> - Connect to specific peer")
    print("  /msg <peer_id> <message> - Send direct message")
    print("  /broadcast <message> - Broadcast to all peers")
    print("  /messages - Show recent messages")
    print("  /quit - Exit")
    print("="*50)
    
    # Auto-discover peers after a short delay
    def auto_discover():
        time.sleep(2)  # Wait for node to start
        print("\\n[System] Auto-discovering peers...")
        node.discover_and_connect_peers()
    
    discover_thread = threading.Thread(target=auto_discover)
    discover_thread.daemon = True
    discover_thread.start()
    
    # Main command loop
    try:
        while True:
            try:
                command = raw_input("\\n[{}] > ".format(args.peer_id)).strip()
                
                if not command:
                    continue
                
                if command.startswith('/'):
                    handle_command(node, command)
                else:
                    # Default: broadcast as chat message
                    node.broadcast_message('chat_message', command)
                    
            except KeyboardInterrupt:
                break
            except EOFError:
                break
                
    except KeyboardInterrupt:
        pass
    
    print("\\n[System] Shutting down...")
    node.stop()

def handle_command(node, command):
    """Handle user commands."""
    parts = command.split(' ', 2)
    cmd = parts[0].lower()
    
    if cmd == '/discover':
        count = node.discover_and_connect_peers()
        print("[System] Discovered {} new peers".format(count))
        
    elif cmd == '/peers':
        peers = node.get_connected_peers()
        if peers:
            print("[System] Connected peers: {}".format(', '.join(peers)))
        else:
            print("[System] No connected peers")
            
    elif cmd == '/connect':
        if len(parts) < 2:
            print("[System] Usage: /connect <peer_id>")
            return
            
        peer_id = parts[1]
        # Need to get peer info from tracker first
        peers = node.get_peers_from_tracker()
        target_peer = None
        
        for peer_info in peers:
            if peer_info['peer_id'] == peer_id:
                target_peer = peer_info
                break
        
        if target_peer:
            if node.connect_to_peer(peer_id, target_peer['ip'], target_peer['port']):
                print("[System] Connected to {}".format(peer_id))
            else:
                print("[System] Failed to connect to {}".format(peer_id))
        else:
            print("[System] Peer {} not found".format(peer_id))
            
    elif cmd == '/msg':
        if len(parts) < 3:
            print("[System] Usage: /msg <peer_id> <message>")
            return
            
        peer_id = parts[1]
        message = parts[2]
        
        if node.send_message(peer_id, 'chat_message', message):
            print("[System] Message sent to {}".format(peer_id))
        else:
            print("[System] Failed to send message to {}".format(peer_id))
            
    elif cmd == '/broadcast':
        if len(parts) < 2:
            print("[System] Usage: /broadcast <message>")
            return
            
        message = ' '.join(parts[1:])
        count = node.broadcast_message('chat_message', message)
        print("[System] Broadcasted to {} peers".format(count))
        
    elif cmd == '/messages':
        messages = node.get_recent_messages(20)
        if messages:
            print("\\n[System] Recent messages:")
            for msg in messages[-10:]:  # Show last 10
                from_peer = msg.get('from_peer', 'unknown')
                content = msg.get('content', '')
                timestamp = msg.get('timestamp', '')
                print("  [{}] {}: {}".format(timestamp[:19], from_peer, content))
        else:
            print("[System] No messages")
            
    elif cmd == '/quit':
        print("[System] Goodbye!")
        sys.exit(0)
        
    else:
        print("[System] Unknown command: {}".format(cmd))
        print("[System] Type /help for available commands")

if __name__ == "__main__":
    main()