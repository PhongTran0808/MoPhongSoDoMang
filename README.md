# 🛰️ WazuhSim — Topology Designer & Lightweight Log Injector

**WazuhSim** là phân hệ giả lập sơ đồ mạng siêu nhẹ & công cụ bắn log tấn công (Log Injector) dành cho **Wazuh Manager THẬT** và **AgentWazuh AI Co-Pilot**.

---

## 🎯 Lý Do & Ranh Giới Thiết Kế

| Vấn đề cũ | Giải pháp WazuhSim |
|---|---|
| Chạy EVE-NG tốn 6-12GB RAM | **Python UDP Syslog Injector**: Tốn ~100MB RAM |
| Giả lập REST API dễ bị sai với đồ thật | **Wazuh Manager THẬT (VMware 172.16.175.145)** xử lý log thật & sinh Alert thật 100% |
| Sơ đồ không đồng bộ với AI | **1-Click Export** đẩy sơ đồ mạng sang `config/known_devices.json` của AgentWazuh |

---

## 🏗️ Cấu Trúc Thư Mục

```text
SoDoMang/
├── backend/
│   ├── main.py                   # FastAPI app (Port 9090)
│   ├── models/
│   │   └── topology_models.py    # Pydantic Schemas (Device, Link, Scenario)
│   ├── routes/
│   │   ├── designer_api.py       # API CRUD sơ đồ
│   │   └── injector_api.py       # API kích hoạt & dừng kịch bản tấn công
│   ├── services/
│   │   ├── topology_store.py     # Đọc/ghi config/topology.json & Export AgentWazuh
│   │   ├── log_injector.py       # Sinh & bắn UDP Syslog port 514
│   │   └── scenario_library.py   # Các kịch bản Brute-force, Scan, Ransomware, DDoS
│   └── requirements.txt
├── frontend/
│   ├── index.html                # Cyber Dark Mode SPA Interface
│   ├── js/                       # Canvas, Panels, API, Scenario logic
│   └── style.css
├── config/
│   └── topology.json             # Nguồn sự thật sơ đồ mạng
└── README.md
```

---

## 🚀 Hướng Dẫn Khởi Chạy

```bash
cd "/run/media/kweismann/Dir_D/Tiểu luận CN/SoDoMang"
pip install -r backend/requirements.txt
python3 backend/main.py
```

Truy cập giao diện UI tại: **`http://127.0.0.1:9090`**

---

## ⚡ Tính Năng Cốt Lõi

1. **Vẽ & Thiết Kế Sơ Đồ Mạng**:
   - Thêm Firewall (FortiGate), Router (Cisco), Switch, Server, Endpoint PC.
   - Chỉnh sửa IP, Tên, Hệ điều hành, Mức độ quan trọng (Asset Criticality 1-10).
   - Kéo-thả sắp xếp vị trí tự do.

2. **1-Click Export sang AgentWazuh**:
   - Nhấp nút **⚡ 1-Click Export** trên thanh công cụ.
   - Danh sách thiết bị tự động được lưu vào `/run/media/kweismann/Dir_D/Tiểu luận CN/AgentWazuh/config/known_devices.json`.
   - AgentWazuh Security Map & Correlation Engine lập tức nhận diện đúng IP và đánh giá Risk Score chính xác!

3. **Bắn Log Syslog UDP 514 Tới Wazuh Manager Thật**:
   - Chọn Kịch bản tấn công (SSH Brute Force, Nmap Port Scan, Ransomware, DDoS).
   - Chọn Thiết bị Nguồn & Thiết bị Đích trực tiếp từ sơ đồ.
   - Nhấp **BẮT ĐẦU** → LogInjector bắn dồn dập các gói UDP Syslog tới `172.16.175.145:514`.
   - Wazuh Manager nhận log, kích hoạt Ruleset thật & đẩy Alert thật cho AgentWazuh AI phân tích!
