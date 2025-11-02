## MỤC TIÊU

Đảm bảo các file server chính có thể **chạy độc lập** và hoạt động đúng:
- ✅ `start_backend.py` - HTTP Server với authentication
- ✅ `start_chatapp.py` - Chat Application với 8 REST APIs
- ✅ `start_proxy.py` - Proxy Server với load balancing
- ⚠️ `start_sampleapp.py` - Sample demo app (optional)

## HƯỚNG DẪN CHẠY SERVERS
### Quick Start - Backend Server:
```powershell
# Terminal 1
cd CO3094-weaprous
python start_backend.py --server-port 9000

# Terminal 2 - Test
Invoke-WebRequest http://localhost:9000/login.html
# Expected: StatusCode 200
```

### Quick Start - Chat Application:
```powershell
# Terminal 1
cd CO3094-weaprous
python start_chatapp.py --server-port 8001

# Terminal 2 - Test
Invoke-WebRequest http://localhost:8001/chat.html
# Expected: StatusCode 200
```

### Quick Start - Proxy Server:
```powershell
# Terminal 1: Backend
cd CO3094-weaprous
python start_backend.py --server-port 9000

# Terminal 2: Proxy
cd CO3094-weaprous
python start_proxy.py --server-port 8080

# Terminal 3: Test
Invoke-WebRequest http://localhost:8080/login.html
# Expected: StatusCode 200 (forwarded from backend)
```

---

## 🎓 DEMO

### Scenario 1: Backend + Authentication
1. Start backend: `python start_backend.py --server-port 9000`
2. Browser: `http://localhost:9000/login.html`
3. Login với **admin/password**
4. Redirect tới index.html (protected)

### Scenario 2: Chat Application
1. Start chat: `python start_chatapp.py --server-port 8001`
2. Browser: `http://localhost:8001/chat.html`
3. Register peer với nickname
4. Send broadcast message
5. View messages trong chat

### Scenario 3: Proxy Load Balancing
1. Start backend: `python start_backend.py --server-port 9000`
2. Start proxy: `python start_proxy.py --server-port 8080`
3. Browser: `http://localhost:8080/login.html`
4. Show proxy forwarding requests

---


