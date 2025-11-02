#
# Test script for WeApRous HTTP Server and Chat Application
# This script tests the functionality of the implemented system
#

import subprocess
import time
import sys
import os
import signal
import threading
import requests
import json

class SystemTester:
    def __init__(self):
        self.processes = []
        self.base_path = r"d:\HK251\MMT\BTL1\CO3094-weaprous"
        self.test_results = {}
        
    def start_process(self, script_name, args=[]):
        """Start a process and return the Popen object."""
        cmd = [sys.executable, script_name] + args
        try:
            print(f"Starting: {' '.join(cmd)}")
            process = subprocess.Popen(
                cmd,
                cwd=self.base_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            self.processes.append(process)
            return process
        except Exception as e:
            print(f"Error starting {script_name}: {e}")
            return None
    
    def test_basic_server_startup(self):
        """Test if servers can start without crashing."""
        print("\\n" + "="*50)
        print("TEST 1: Basic Server Startup")
        print("="*50)
        
        # Test backend server
        print("\\n1.1 Testing Backend Server...")
        backend_process = self.start_process("start_backend.py", ["--server-port", "9000"])
        time.sleep(2)
        
        if backend_process and backend_process.poll() is None:
            print("✅ Backend server started successfully")
            self.test_results['backend_startup'] = True
        else:
            print("❌ Backend server failed to start")
            self.test_results['backend_startup'] = False
            if backend_process:
                stderr = backend_process.stderr.read()
                print(f"Error: {stderr}")
        
        # Test proxy server
        print("\\n1.2 Testing Proxy Server...")
        proxy_process = self.start_process("start_proxy.py", ["--server-port", "8080"])
        time.sleep(2)
        
        if proxy_process and proxy_process.poll() is None:
            print("✅ Proxy server started successfully")
            self.test_results['proxy_startup'] = True
        else:
            print("❌ Proxy server failed to start")
            self.test_results['proxy_startup'] = False
            if proxy_process:
                stderr = proxy_process.stderr.read()
                print(f"Error: {stderr}")
        
        # Test chat server
        print("\\n1.3 Testing Chat Server...")
        chat_process = self.start_process("start_chatapp.py", ["--server-port", "8001"])
        time.sleep(2)
        
        if chat_process and chat_process.poll() is None:
            print("✅ Chat server started successfully")
            self.test_results['chat_startup'] = True
        else:
            print("❌ Chat server failed to start")
            self.test_results['chat_startup'] = False
            if chat_process:
                stderr = chat_process.stderr.read()
                print(f"Error: {stderr}")
        
        return all([
            self.test_results.get('backend_startup', False),
            self.test_results.get('proxy_startup', False),
            self.test_results.get('chat_startup', False)
        ])
    
    def test_http_endpoints(self):
        """Test HTTP endpoints are responding."""
        print("\\n" + "="*50)
        print("TEST 2: HTTP Endpoints")
        print("="*50)
        
        # Give servers time to start
        time.sleep(3)
        
        # Test backend direct access
        print("\\n2.1 Testing Backend Direct Access...")
        try:
            response = requests.get("http://localhost:9000/", timeout=5)
            if response.status_code in [200, 401, 404]:  # Any response is good
                print("✅ Backend responds to HTTP requests")
                self.test_results['backend_http'] = True
            else:
                print(f"⚠️ Backend returned unexpected status: {response.status_code}")
                self.test_results['backend_http'] = False
        except Exception as e:
            print(f"❌ Backend HTTP test failed: {e}")
            self.test_results['backend_http'] = False
        
        # Test proxy access
        print("\\n2.2 Testing Proxy Access...")
        try:
            response = requests.get("http://localhost:8080/", 
                                  headers={'Host': 'localhost:8080'}, 
                                  timeout=5)
            if response.status_code in [200, 401, 404]:
                print("✅ Proxy forwards requests to backend")
                self.test_results['proxy_http'] = True
            else:
                print(f"⚠️ Proxy returned unexpected status: {response.status_code}")
                self.test_results['proxy_http'] = False
        except Exception as e:
            print(f"❌ Proxy HTTP test failed: {e}")
            self.test_results['proxy_http'] = False
        
        # Test chat API
        print("\\n2.3 Testing Chat API...")
        try:
            response = requests.get("http://localhost:8001/get-list", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if 'status' in data:
                    print("✅ Chat API responds correctly")
                    self.test_results['chat_api'] = True
                else:
                    print("⚠️ Chat API response format incorrect")
                    self.test_results['chat_api'] = False
            else:
                print(f"❌ Chat API returned status: {response.status_code}")
                self.test_results['chat_api'] = False
        except Exception as e:
            print(f"❌ Chat API test failed: {e}")
            self.test_results['chat_api'] = False
    
    def test_authentication(self):
        """Test authentication functionality."""
        print("\\n" + "="*50)
        print("TEST 3: Authentication")
        print("="*50)
        
        # Test login endpoint
        print("\\n3.1 Testing Login Functionality...")
        try:
            # Test invalid login
            login_data = {
                'username': 'wrong',
                'password': 'wrong'
            }
            response = requests.post("http://localhost:9000/login", 
                                   data=login_data, timeout=5)
            
            if response.status_code == 401:
                print("✅ Invalid login correctly rejected")
                
                # Test valid login
                valid_data = {
                    'username': 'admin', 
                    'password': 'password'
                }
                response = requests.post("http://localhost:9000/login", 
                                       data=valid_data, timeout=5)
                
                if response.status_code == 200 and 'Set-Cookie' in response.headers:
                    print("✅ Valid login accepted with cookie")
                    self.test_results['authentication'] = True
                else:
                    print(f"⚠️ Valid login issue: {response.status_code}")
                    self.test_results['authentication'] = False
            else:
                print(f"❌ Authentication test failed: {response.status_code}")
                self.test_results['authentication'] = False
                
        except Exception as e:
            print(f"❌ Authentication test error: {e}")
            self.test_results['authentication'] = False
    
    def test_chat_functionality(self):
        """Test chat application functionality."""
        print("\\n" + "="*50)
        print("TEST 4: Chat Functionality")
        print("="*50)
        
        # Test peer registration
        print("\\n4.1 Testing Peer Registration...")
        try:
            peer_data = {
                'peer_id': 'test_user_1',
                'ip': '127.0.0.1',
                'port': 9999
            }
            
            response = requests.post("http://localhost:8001/submit-info",
                                   json=peer_data, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    print("✅ Peer registration successful")
                    self.test_results['peer_registration'] = True
                else:
                    print(f"⚠️ Peer registration failed: {data.get('message')}")
                    self.test_results['peer_registration'] = False
            else:
                print(f"❌ Peer registration HTTP error: {response.status_code}")
                self.test_results['peer_registration'] = False
                
        except Exception as e:
            print(f"❌ Peer registration error: {e}")
            self.test_results['peer_registration'] = False
        
        # Test peer discovery
        print("\\n4.2 Testing Peer Discovery...")
        try:
            response = requests.get("http://localhost:8001/get-list", timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success' and 'peers' in data:
                    peers = data['peers']
                    if len(peers) > 0:
                        print(f"✅ Found {len(peers)} registered peers")
                        self.test_results['peer_discovery'] = True
                    else:
                        print("⚠️ No peers found (expected after registration)")
                        self.test_results['peer_discovery'] = False
                else:
                    print(f"⚠️ Peer discovery format error: {data}")
                    self.test_results['peer_discovery'] = False
            else:
                print(f"❌ Peer discovery HTTP error: {response.status_code}")
                self.test_results['peer_discovery'] = False
                
        except Exception as e:
            print(f"❌ Peer discovery error: {e}")
            self.test_results['peer_discovery'] = False
        
        # Test message broadcasting
        print("\\n4.3 Testing Message Broadcasting...")
        try:
            message_data = {
                'from_peer': 'test_user_1',
                'message': 'Hello, this is a test message!',
                'channel': 'general'
            }
            
            response = requests.post("http://localhost:8001/broadcast-peer",
                                   json=message_data, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    print("✅ Message broadcasting successful")
                    self.test_results['message_broadcasting'] = True
                else:
                    print(f"⚠️ Broadcasting failed: {data.get('message')}")
                    self.test_results['message_broadcasting'] = False
            else:
                print(f"❌ Broadcasting HTTP error: {response.status_code}")
                self.test_results['message_broadcasting'] = False
                
        except Exception as e:
            print(f"❌ Broadcasting error: {e}")
            self.test_results['message_broadcasting'] = False
    
    def cleanup(self):
        """Clean up all started processes."""
        print("\\n" + "="*50)
        print("CLEANUP: Stopping all processes...")
        print("="*50)
        
        for i, process in enumerate(self.processes):
            try:
                if process.poll() is None:  # Process is still running
                    print(f"Stopping process {i+1}...")
                    process.terminate()
                    time.sleep(1)
                    
                    if process.poll() is None:  # Still running, force kill
                        process.kill()
                        print(f"Force killed process {i+1}")
                    else:
                        print(f"Process {i+1} stopped gracefully")
                        
            except Exception as e:
                print(f"Error stopping process {i+1}: {e}")
        
        self.processes.clear()
    
    def print_summary(self):
        """Print test summary."""
        print("\\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result)
        
        print(f"\\nTotal Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%" if total_tests > 0 else "No tests run")
        
        print("\\nDetailed Results:")
        for test_name, result in self.test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"  {test_name:20} : {status}")
        
        if passed_tests == total_tests:
            print("\\n🎉 All tests passed! The system is working correctly.")
        elif passed_tests > total_tests * 0.7:
            print("\\n✨ Most tests passed! System is mostly functional.")
        else:
            print("\\n⚠️ Several tests failed. Please check the implementation.")
    
    def run_all_tests(self):
        """Run all tests in sequence."""
        try:
            print("🚀 Starting WeApRous System Tests...")
            print("This will test the HTTP server and chat application components.")
            
            # Test 1: Server startup
            if not self.test_basic_server_startup():
                print("\\n⚠️ Server startup issues detected. Continuing with available servers...")
            
            # Test 2: HTTP endpoints
            self.test_http_endpoints()
            
            # Test 3: Authentication
            self.test_authentication()
            
            # Test 4: Chat functionality
            self.test_chat_functionality()
            
            # Summary
            self.print_summary()
            
        except KeyboardInterrupt:
            print("\\n\\nTests interrupted by user.")
        except Exception as e:
            print(f"\\n\\nUnexpected error during testing: {e}")
        finally:
            self.cleanup()

def main():
    tester = SystemTester()
    tester.run_all_tests()

if __name__ == "__main__":
    main()