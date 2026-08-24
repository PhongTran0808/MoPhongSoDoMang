import subprocess
import json
import re
import logging
from typing import Dict, Any, List
from pathlib import Path

logger = logging.getLogger("ContainerService")

BASE_DIR = Path(__file__).resolve().parent.parent.parent
TOPOLOGY_JSON_PATH = BASE_DIR / "config" / "topology.json"

PRIMARY_5_DEVICES = {
    "DMZ-Server-Main",
    "DNS-Server",
    "Manager-Admin-PC",
    "PC-PB1-VLAN10",
    "Dell-R760-DR"
}

def sanitize_container_name(name: str) -> str:
    """Tạo tên container hợp lệ từ tên thiết bị."""
    sanitized = re.sub(r'[^a-zA-Z0-9_-]', '_', name)
    return f"wazuh-agent-{sanitized}"

def get_container_status(device_name: str) -> Dict[str, Any]:
    """Kiểm tra trạng thái container của thiết bị."""
    container_name = sanitize_container_name(device_name)
    try:
        cmd = ["docker", "inspect", container_name]
        res = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if res.returncode != 0:
            return {
                "exists": False,
                "status": "not_created",
                "container_name": container_name,
                "wazuh_manager": None
            }
        
        data = json.loads(res.stdout)
        if not data:
            return {
                "exists": False,
                "status": "not_created",
                "container_name": container_name,
                "wazuh_manager": None
            }

        state = data[0].get("State", {})
        running = state.get("Running", False)
        paused = state.get("Paused", False)
        
        # Lấy IP Wazuh Manager từ env vars
        env_list = data[0].get("Config", {}).get("Env", [])
        wazuh_mgr = "172.16.175.145"
        for env in env_list:
            if env.startswith("WAZUH_MANAGER_SERVER="):
                wazuh_mgr = env.split("=", 1)[1]
                break

        status_str = "running" if running else ("paused" if paused else "stopped")

        return {
            "exists": True,
            "status": status_str,
            "container_name": container_name,
            "wazuh_manager": wazuh_mgr,
            "started_at": state.get("StartedAt")
        }
    except Exception as e:
        logger.error(f"Lỗi kiểm tra container {container_name}: {e}")
        return {
            "exists": False,
            "status": "error",
            "error": str(e),
            "container_name": container_name
        }

def create_container(device_name: str, wazuh_manager_ip: str, device_ip: str = None, enroll_pass: str = None) -> Dict[str, Any]:
    """Tạo và chạy Docker Container cho 1 node thiết bị với IP & Mã đăng ký khớp sơ đồ."""
    container_name = sanitize_container_name(device_name)
    wazuh_ip = wazuh_manager_ip.strip() if wazuh_manager_ip else "172.16.175.145"

    # Nếu container đã tồn tại thì xóa trước để khởi tạo mới
    subprocess.run(["docker", "rm", "-f", container_name], capture_output=True, text=True, check=False)

    cmd = [
        "docker", "run", "-d",
        "--name", container_name,
        "-h", device_name[:63],  # Hostname max 63 chars
        "-e", f"WAZUH_MANAGER_SERVER={wazuh_ip}",
        "-e", f"WAZUH_AGENT_NAME={device_name}",
        "--restart", "always"
    ]

    if enroll_pass and enroll_pass.strip():
        cmd.extend(["-e", f"WAZUH_REGISTRATION_PASSWORD={enroll_pass.strip()}"])

    cmd.append("wazuh/wazuh-agent:4.14.7")

    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if res.returncode == 0:
            # Nếu có device_ip từ sơ đồ, chèn <agent_address> vào ossec.conf để Wazuh Manager nhận diện đúng IP sơ đồ
            if device_ip and device_ip.strip():
                import time
                time.sleep(1.5)
                target_ip = device_ip.strip()
                sed_cmd = [
                    "docker", "exec", container_name,
                    "sed", "-i",
                    f"s#<agent_name>{device_name}</agent_name>#<agent_name>{device_name}</agent_name>\\n      <agent_address>{target_ip}</agent_address>#g",
                    "/var/ossec/etc/ossec.conf"
                ]
                subprocess.run(sed_cmd, capture_output=True, text=True, check=False)
                # Restart wazuh agent daemon inside container to pick up new config
                subprocess.run(["docker", "exec", container_name, "/var/ossec/bin/wazuh-control", "restart"], capture_output=True, text=True, check=False)

            return {
                "status": "success",
                "message": f"🟢 Đã khởi tạo Container {container_name} (IP: {device_ip or 'Auto'}) kết nối tới Wazuh Manager {wazuh_ip}",
                "container_id": res.stdout.strip()[:12]
            }
        else:
            return {
                "status": "error",
                "message": f"🔴 Lỗi khởi tạo container: {res.stderr.strip()}"
            }
    except Exception as e:
        return {"status": "error", "message": f"🔴 Lỗi thực thi Docker: {str(e)}"}

def toggle_container(device_name: str, action: str) -> Dict[str, Any]:
    """Bật (start), Tạm dừng (stop) hoặc Xóa (remove) container."""
    container_name = sanitize_container_name(device_name)
    
    if action == "start":
        cmd = ["docker", "start", container_name]
        msg_ok = f"🟢 Đã bật container {container_name} (Hoạt động)"
    elif action == "stop":
        cmd = ["docker", "stop", container_name]
        msg_ok = f"⏸️ Đã tạm dừng container {container_name}"
    elif action == "remove":
        cmd = ["docker", "rm", "-f", container_name]
        msg_ok = f"🗑️ Đã xóa container {container_name}"
    else:
        return {"status": "error", "message": "Hành động không hợp lệ"}

    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if res.returncode == 0:
            return {"status": "success", "message": msg_ok}
        else:
            return {"status": "error", "message": f"Lỗi Docker: {res.stderr.strip()}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def batch_create_all_containers(wazuh_manager_ip: str, enroll_pass: str = None) -> Dict[str, Any]:
    """Khởi tạo toàn bộ Container cho tất cả node trong sơ đồ mạng."""
    if not TOPOLOGY_JSON_PATH.exists():
        return {"status": "error", "message": "Không tìm thấy topology.json"}

    try:
        topo_data = json.loads(TOPOLOGY_JSON_PATH.read_text(encoding="utf-8"))
        devices = topo_data.get("devices", [])
    except Exception as e:
        return {"status": "error", "message": f"Lỗi đọc topology.json: {e}"}

    created_count = 0
    running_count = 0
    stopped_count = 0

    for dev in devices:
        name = dev.get("name")
        dev_type = dev.get("type", "").lower()
        if not name or dev_type in ["cloud", "wazuh"]:
            continue

        ip = dev.get("ip")
        res = create_container(name, wazuh_manager_ip, device_ip=ip, enroll_pass=enroll_pass)
        if res.get("status") == "success":
            created_count += 1
            # 5 node chính thì giữ chạy, các node khác tạm dừng (stop)
            if name in PRIMARY_5_DEVICES:
                running_count += 1
            else:
                toggle_container(name, "stop")
                stopped_count += 1

    return {
        "status": "success",
        "message": f"🎉 THÀNH CÔNG! Đã tạo {created_count} container cho tất cả các node trong sơ đồ.\n- {running_count} node chính đang CHẠY (Active).\n- {stopped_count} node còn lại ở trạng thái ĐÃ TẠO (Stopped - 0% RAM/CPU), bạn có thể nhấp BẬT bất cứ lúc nào!",
        "created_total": created_count,
        "running_primary": running_count,
        "stopped_idle": stopped_stopped_count if 'stopped_stopped_count' in locals() else stopped_count
    }
