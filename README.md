## MỤC TIÊU

Đảm bảo các file server chính có thể **chạy độc lập** và hoạt động đúng trên môi trường mạng thực tế (IP: 10.130.23.14):
- ✅ `start_backend.py` - HTTP Server với authentication
- ✅ `start_chatapp.py` - Chat Application với 8 REST APIs
- ✅ `start_proxy.py` - Proxy Server với load balancing
- ⚠️ `start_sampleapp.py` - Sample demo app (optional)

> **LƯU Ý QUAN TRỌNG:**
> - Địa chỉ IP hiện tại: **10.130.23.14** (Lấy từ `ipconfig` Wi-Fi)
> - Nếu IP máy thay đổi, cần cập nhật lại file `config/proxy.conf` và các lệnh bên dưới.

## HƯỚNG DẪN CHẠY SERVERS

### 1. Quick Start - Backend Server
Server xử lý logic chính, chạy tại port 9000.

```powershell
# Terminal 1
 
python start_backend.py --server-ip 10.130.23.14 --server-port 9000

# Terminal 2 - Test (Mở PowerShell khác để test)
Invoke-WebRequest http://10.130.23.14:9000/login.html
# (http://10.130.23.14:9000/login.html)
# Expected: StatusCode 200

2. Quick Start - Chat Application
Ứng dụng chat P2P/Hybrid, chạy tại port 8001.

# Terminal 1
 
python start_chatapp.py --server-ip 10.130.23.14 --server-port 8001

# Terminal 2 - Test
Invoke-WebRequest http://10.130.23.14:8001/chat.html
# (http://10.130.23.14:8001/chat.html)
# Expected: StatusCode 200

3. Quick Start - Proxy Server
Chạy mô hình đầy đủ: Client -> Proxy (8080) -> Backend (9000). Yêu cầu: Cần cấu hình config/proxy.conf trỏ về 10.130.23.14:9000 trước.

# Terminal 1: Chạy Backend trước
 
python start_backend.py --server-ip 10.130.23.14 --server-port 9000

# Terminal 2: Chạy Proxy
 
python start_proxy.py --server-ip 10.130.23.14 --server-port 8080

# Terminal 3: Test truy cập qua Proxy
Invoke-WebRequest http://10.130.23.14:8080/login.html
# (http://10.130.23.14:8080/login.html)
# Expected: StatusCode 200 (Được forward từ backend)


🎓 DEMO SCENARIOS (Trên Trình Duyệt)
Scenario 1: Backend + Authentication
    Start backend: python start_backend.py --server-ip 10.130.23.14 --server-port 9000

    Mở trình duyệt: http://10.130.23.14:9000/login.html

    Login với admin/password

    Hệ thống sẽ redirect tới index.html (protected resource).

Scenario 2: Chat Application
    Start chat: python start_chatapp.py --server-ip 10.130.23.14 --server-port 8001

    Mở trình duyệt: http://10.130.23.14:8001/chat.html

    Nhập Nickname để Register peer.

    Gửi tin nhắn broadcast hoặc chat trực tiếp.

Scenario 3: Proxy Load Balancing
    Start backend: python start_backend.py --server-ip 10.130.23.14 --server-port 9000

    Start proxy: python start_proxy.py --server-ip 10.130.23.14 --server-port 8080

    Mở trình duyệt truy cập qua Proxy: http://10.130.23.14:8080/login.html

    Quan sát log tại Terminal 2 (Proxy) để thấy request được chuyển tiếp (forwarding) xuống Backend.