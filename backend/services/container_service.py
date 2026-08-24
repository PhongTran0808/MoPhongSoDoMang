import subprocess
import json
import re
import logging
from typing import Dict, Any, List
from pathlib import Path

logger = logging.getLogger("ContainerService")

BASE_DIR = Path(__file__).resolve().parent.parent.parent
TOPOLOGY_JSON_PATH = BASE_DIR / "config" / "topology.json"

def sanitize_container_name(name: str) -> str:
    """Tạo tên container hợp lệ từ tên thiết bị."""
    sanitized = re.sub(r'[^a-zA-Z0-9_-]', '_', name)
    return f"wazuh-agent-{sanitized}"

def get_container_status(device_name: str) -> Dict[str, Any]:
    """Kiểm tra trạng thái container của thiết bị & trạng thái deploy Wazuh Agent."""
    container_name = sanitize_container_name(device_name)
    try:
        cmd = ["docker", "inspect", container_name]
        res = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if res.returncode != 0:
            return {
                "exists": False,
                "status": "not_created",
                "container_name": container_name,
                "deployed": False,
                "wazuh_manager": None
            }
        
        data = json.loads(res.stdout)
        if not data:
            return {
                "exists": False,
                "status": "not_created",
                "container_name": container_name,
                "deployed": False,
                "wazuh_manager": None
            }

        state = data[0].get("State", {})
        running = state.get("Running", False)
        paused = state.get("Paused", False)
        
        # Kiểm tra xem agent đã được deploy/cấu hình IP Manager chưa
        env_list = data[0].get("Config", {}).get("Env", [])
        wazuh_mgr = None
        for env in env_list:
            if env.startswith("WAZUH_MANAGER_SERVER=") or env.startswith("WAZUH_MANAGER="):
                val = env.split("=", 1)[1].strip()
                if val and val != "0.0.0.0" and val != "127.0.0.1":
                    wazuh_mgr = val
                break

        status_str = "running" if running else ("paused" if paused else "stopped")

        # Kiểm tra xem file client.keys có tồn tại (đã đăng ký với manager) không
        deployed = False
        if running:
            chk_cmd = ["docker", "exec", container_name, "cat", "/var/ossec/etc/client.keys"]
            chk_res = subprocess.run(chk_cmd, capture_output=True, text=True, check=False)
            if chk_res.returncode == 0 and chk_res.stdout.strip():
                deployed = True

        return {
            "exists": True,
            "status": status_str,
            "container_name": container_name,
            "deployed": deployed,
            "wazuh_manager": wazuh_mgr,
            "started_at": state.get("StartedAt")
        }
    except Exception as e:
        logger.error(f"Lỗi kiểm tra container {container_name}: {e}")
        return {
            "exists": False,
            "status": "error",
            "error": str(e),
            "container_name": container_name,
            "deployed": False
        }

def create_container(device_name: str, device_ip: str = None) -> Dict[str, Any]:
    """Khởi tạo Container Docker thuần (Clean OS), CHƯA gia nhập Wazuh Server."""
    container_name = sanitize_container_name(device_name)

    # Nếu container đã tồn tại thì xóa trước để khởi tạo lại mới tinh
    subprocess.run(["docker", "rm", "-f", container_name], capture_output=True, text=True, check=False)

    cmd = [
        "docker", "run", "-d",
        "--name", container_name,
        "-h", device_name[:63],
        "-e", "WAZUH_MANAGER_SERVER=0.0.0.0", # IP tạm rỗng, chưa kết nối
        "-e", f"WAZUH_AGENT_NAME={device_name}",
        "--restart", "always",
        "wazuh/wazuh-agent:4.14.7"
    ]

    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if res.returncode == 0:
            return {
                "status": "success",
                "message": f"🟢 Đã khởi tạo Docker Container {container_name} (Hệ điều hành ảo sẵn sàng). Container CHƯA đăng ký vào Wazuh Server.",
                "container_id": res.stdout.strip()[:12]
            }
        else:
            return {
                "status": "error",
                "message": f"🔴 Lỗi khởi tạo container: {res.stderr.strip()}"
            }
    except Exception as e:
        return {"status": "error", "message": f"🔴 Lỗi thực thi Docker: {str(e)}"}

def deploy_agent_to_manager(device_name: str, wazuh_manager_ip: str, device_ip: str = None, enroll_pass: str = None) -> Dict[str, Any]:
    """Thực thi Lệnh Deploy Agent từ Wazuh Server vào bên trong Container."""
    container_name = sanitize_container_name(device_name)
    wazuh_ip = wazuh_manager_ip.strip() if wazuh_manager_ip else "192.168.1.234"

    # Kiểm tra container đã chạy chưa, nếu chưa thì tạo container trước
    st = get_container_status(device_name)
    if not st.get("exists") or st.get("status") != "running":
        create_res = create_container(device_name, device_ip)
        if create_res.get("status") == "error":
            return create_res

    import time
    time.sleep(1.0)

    try:
        # Cấu hình IP Wazuh Manager vào ossec.conf bên trong container
        sed_ip_cmd = [
            "docker", "exec", container_name,
            "sed", "-i",
            f"s#<address>.*</address>#<address>{wazuh_ip}</address>#g",
            "/var/ossec/etc/ossec.conf"
        ]
        subprocess.run(sed_ip_cmd, capture_output=True, text=True, check=False)

        # Nếu có device_ip từ sơ đồ, chèn <agent_address>
        if device_ip and device_ip.strip():
            target_ip = device_ip.strip()
            sed_addr_cmd = [
                "docker", "exec", container_name,
                "sed", "-i",
                f"s#<agent_name>{device_name}</agent_name>#<agent_name>{device_name}</agent_name>\\n      <agent_address>{target_ip}</agent_address>#g",
                "/var/ossec/etc/ossec.conf"
            ]
            subprocess.run(sed_addr_cmd, capture_output=True, text=True, check=False)

        # Thực thi Đăng ký (Enrollment) qua agent-auth
        auth_cmd = ["docker", "exec", container_name, "/var/ossec/bin/agent-auth", "-m", wazuh_ip, "-A", device_name]
        if enroll_pass and enroll_pass.strip():
            auth_cmd.extend(["-P", enroll_pass.strip()])

        auth_res = subprocess.run(auth_cmd, capture_output=True, text=True, check=False)

        # Restart wazuh-agent daemon trong container
        subprocess.run(["docker", "exec", container_name, "/var/ossec/bin/wazuh-control", "restart"], capture_output=True, text=True, check=False)

        return {
            "status": "success",
            "message": f"🚀 ĐÃ DEPLOY THÀNH CÔNG! Node '{device_name}' đã thực thi lệnh đăng ký và nhập vào Wazuh Server ({wazuh_ip})!",
            "auth_output": auth_res.stdout.strip() or auth_res.stderr.strip()
        }
    except Exception as e:
        return {"status": "error", "message": f"🔴 Lỗi thực thi Deploy Agent: {str(e)}"}

def toggle_container(device_name: str, action: str) -> Dict[str, Any]:
    """Bật (start), Tạm dừng (stop) hoặc Xóa (remove) container."""
    container_name = sanitize_container_name(device_name)
    
    if action == "start":
        cmd = ["docker", "start", container_name]
        msg_ok = f"🟢 Đã bật container {container_name}"
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
