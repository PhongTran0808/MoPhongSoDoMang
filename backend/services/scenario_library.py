import time
import logging
from typing import Dict, Any, List, Optional
from backend.models.topology_models import DeviceModel, ScenarioRequest
from backend.services.log_injector import LogInjector

logger = logging.getLogger("ScenarioLibrary")

# Global runner state
SCENARIO_RUNNING_STATE = {
    "is_running": False,
    "scenario_id": None,
    "current_step": 0,
    "total_steps": 0,
    "logs_sent": 0,
    "status": "idle",
    "last_log": ""
}


def get_available_scenarios() -> List[Dict[str, Any]]:
    """Trả về danh sách các kịch bản tấn công có sẵn."""
    return [
        {
            "id": "ssh_brute_force",
            "name": "💥 SSH Brute-Force Attack",
            "description": "Gửi 30 log đăng nhập thất bại SSH từ Nguồn tới Đích, sau đó 1 log thành công. Kích hoạt Wazuh Rules 5763 (Brute force) & 5715.",
            "recommended_target_os": "Linux"
        },
        {
            "id": "nmap_port_scan",
            "name": "🔍 Nmap Port Scan & Reconnaissance",
            "description": "Gửi 50 log FortiGate/Cisco deny traffic trên nhiều port khác nhau. Kích hoạt Wazuh Rule 4151 (Port scan detected).",
            "recommended_target_os": "Any"
        },
        {
            "id": "windows_ransomware",
            "name": "☣️ Ransomware Activity Simulation",
            "description": "Gửi 25 log Windows Event (Event 4663) ghi nhận quá trình mã hóa & đổi tên file hàng loạt. Kích hoạt Wazuh High-severity Alert.",
            "recommended_target_os": "Windows"
        },
        {
            "id": "ddos_flood",
            "name": "🌊 Volumetric DDoS Traffic Flood",
            "description": "Bắn 100 gói log lưu lượng cao dồn dập trong 5 giây tới Firewall/Server để thử khả năng correlation của Wazuh.",
            "recommended_target_os": "Any"
        }
    ]


def run_scenario_task(req: ScenarioRequest, src_device: DeviceModel, target_device: DeviceModel):
    """Execution loop for attack scenarios (runs in background or thread)."""
    global SCENARIO_RUNNING_STATE

    SCENARIO_RUNNING_STATE["is_running"] = True
    SCENARIO_RUNNING_STATE["scenario_id"] = req.scenario_id
    SCENARIO_RUNNING_STATE["current_step"] = 0
    SCENARIO_RUNNING_STATE["total_steps"] = req.burst_count
    SCENARIO_RUNNING_STATE["logs_sent"] = 0
    SCENARIO_RUNNING_STATE["status"] = f"Đang chạy {req.scenario_id} từ {src_device.name} -> {target_device.name}"

    injector = LogInjector(wazuh_host=req.wazuh_host, wazuh_port=req.wazuh_syslog_port)

    try:
        if req.scenario_id == "ssh_brute_force":
            total = req.burst_count
            for i in range(total):
                if not SCENARIO_RUNNING_STATE["is_running"]:
                    break
                is_last = (i == total - 1)
                log_msg = injector.generate_ssh_brute_force_log(src_device, target_device, success=is_last)
                injector.send_raw_syslog(log_msg)
                
                SCENARIO_RUNNING_STATE["current_step"] = i + 1
                SCENARIO_RUNNING_STATE["logs_sent"] += 1
                SCENARIO_RUNNING_STATE["last_log"] = log_msg
                time.sleep(0.3)  # Send log every 300ms

        elif req.scenario_id == "nmap_port_scan":
            total = req.burst_count
            for i in range(total):
                if not SCENARIO_RUNNING_STATE["is_running"]:
                    break
                log_msg = injector.generate_fortigate_firewall_log(src_device, target_device, action="deny")
                injector.send_raw_syslog(log_msg)
                
                SCENARIO_RUNNING_STATE["current_step"] = i + 1
                SCENARIO_RUNNING_STATE["logs_sent"] += 1
                SCENARIO_RUNNING_STATE["last_log"] = log_msg
                time.sleep(0.1)  # High speed scan (100ms)

        elif req.scenario_id == "windows_ransomware":
            total = req.burst_count
            for i in range(total):
                if not SCENARIO_RUNNING_STATE["is_running"]:
                    break
                log_msg = injector.generate_ransomware_log(src_device, target_device)
                injector.send_raw_syslog(log_msg)
                
                SCENARIO_RUNNING_STATE["current_step"] = i + 1
                SCENARIO_RUNNING_STATE["logs_sent"] += 1
                SCENARIO_RUNNING_STATE["last_log"] = log_msg
                time.sleep(0.15)

        elif req.scenario_id == "ddos_flood":
            total = req.burst_count
            for i in range(total):
                if not SCENARIO_RUNNING_STATE["is_running"]:
                    break
                log_msg = injector.generate_fortigate_firewall_log(src_device, target_device, action="deny")
                injector.send_raw_syslog(log_msg)
                
                SCENARIO_RUNNING_STATE["current_step"] = i + 1
                SCENARIO_RUNNING_STATE["logs_sent"] += 1
                SCENARIO_RUNNING_STATE["last_log"] = log_msg
                time.sleep(0.05)  # Very fast flood (50ms)

        SCENARIO_RUNNING_STATE["status"] = f"Hoàn tất kịch bản {req.scenario_id}! Đã gửi {SCENARIO_RUNNING_STATE['logs_sent']} log."
    except Exception as e:
        logger.error(f"Error during scenario execution: {e}")
        SCENARIO_RUNNING_STATE["status"] = f"Lỗi kịch bản: {e}"
    finally:
        SCENARIO_RUNNING_STATE["is_running"] = False


def stop_current_scenario():
    """Dừng kịch bản đang chạy."""
    global SCENARIO_RUNNING_STATE
    SCENARIO_RUNNING_STATE["is_running"] = False
    SCENARIO_RUNNING_STATE["status"] = "Đã dừng kịch bản thủ công."
