# 🌐 SODOMANG — 38-NODE NETWORK TOPOLOGY & DOCKER MANAGER

## 📌 1. TỔNG QUAN HỆ THỐNG SODOMANG

**SoDoMang** là nền tảng thiết kế sơ đồ mạng động (Dynamic Network Topology Visualizer) tích hợp trình quản lý Docker Container (Docker Container Orchestrator). Hệ thống cho phép trực quan hóa hơn 38 thiết bị mạng doanh nghiệp (Tường lửa FortiGate, Switch Cisco Catalyst, DMZ Web Server, Workstation các VLAN 10-60, Branch Offices, Wazuh Manager) và đồng bộ trực tiếp sang AgentWazuh để giám sát SOC AI.

---

## 🏗️ 2. KIẾN TRÚC VÀ CÁC THÀNH PHẦN SODOMANG

### 2.1 Cổng dịch vụ (Ports)
- **Port 9090**: Giao diện UI Vis.js & FastAPI Backend Server (`backend/main.py`).

### 2.2 Structure Thư mục
```text
SoDoMang/
├── backend/
│   └── main.py              # FastAPI server (Port 9090), Static Fallback Route, REST APIs
├── frontend/
│   ├── index.html           # HTML5 UI, Embedded Cyber Dark CSS, Vis-Network Topology Engine
│   └── style.css            # Stylesheet mở rộng
└── config/
    └── topology.json        # Cơ sở dữ liệu JSON lưu trữ 38 thiết bị & liên kết mạng
```

---

## 🚀 3. HƯỚNG DẪN KHỞI ĐỘNG HỆ THỐNG (RUNNING PROCEDURE)

### 3.1 Khởi động độc lập SoDoMang (Port 9090)
```bash
cd "/run/media/kweismann/Dir_D/Tiểu luận CN/SoDoMang"
python3 backend/main.py
```

### 3.2 Khởi động đồng thời cả AgentWazuh (8080) và SoDoMang (9090)
```bash
python3 /tmp/start_agentwazuh_and_sodomang.py
```

---

## 🛠️ 4. CÁC LỖI THƯỜNG GẶP VÀ CÁCH KHẮC PHỤC (TROUBLESHOOTING & KNOWN BUGS)

### 🔴 Lỗi 1: Giao diện vỡ CSS ("bị vỡ cSS / Lỗi hiển thị trên HTML")
- **Nguyên nhân**: FastAPI không load được file `style.css` khi truy cập ở đường dẫn gốc `/style.css`.
- **Khắc phục**:
  1. Nhúng trực tiếp toàn bộ CSS vào thẻ `<style>` trong `frontend/index.html`.
  2. Thêm route fallback trong `backend/main.py`:
     ```python
     @app.get("/style.css")
     async def serve_root_static():
         return FileResponse("frontend/style.css")
     ```

### 🔴 Lỗi 2: Không đồng bộ được thiết bị sang AgentWazuh
- **Nguyên nhân**: `AgentWazuh/config/known_devices.json` hoặc IP Wazuh Manager trong `topology.json` bị lệch.
- **Khắc phục**: Chạy tính năng 1-Click Export từ UI Port 9090 hoặc chạy script đồng bộ `/tmp/update_wazuh_210_monitoring.py`.
