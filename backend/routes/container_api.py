import re
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from backend.services.container_service import (
    get_container_status,
    create_container,
    deploy_agent_to_manager,
    batch_deploy_agents_to_manager,
    toggle_container,
    create_micro_linux_target,
    simulate_malware_checkhash,
    get_agent_ai_flow_data
)

router = APIRouter(prefix="/api/container", tags=["Container Manager"])

class ContainerCreateRequest(BaseModel):
    device_name: str
    device_ip: Optional[str] = None

class ContainerDeployRequest(BaseModel):
    device_name: str
    wazuh_manager_ip: str
    device_ip: Optional[str] = None
    enroll_pass: Optional[str] = None

class BatchDeployRequest(BaseModel):
    device_names: List[str]
    wazuh_manager_ip: Optional[str] = "192.168.1.201"

class ContainerToggleRequest(BaseModel):
    device_name: str
    action: str  # "start", "stop", "remove"

class MicroLinuxSimulateRequest(BaseModel):
    device_name: Optional[str] = "Micro-Linux-64MB-Target"
    payload_type: Optional[str] = "suspicious_binary"

@router.get("/status/{device_name:path}")
def check_status(device_name: str):
    """Lấy trạng thái Docker container & trạng thái Deploy của 1 thiết bị."""
    return get_container_status(device_name)

@router.post("/create")
def create_node_container(req: ContainerCreateRequest):
    """Khởi tạo Container Docker thuần (Clean OS). CHƯA gia nhập Wazuh Server."""
    res = create_container(req.device_name, req.device_ip)
    if res.get("status") == "error":
        raise HTTPException(status_code=500, detail=res.get("message"))
    return res

@router.post("/deploy-agent")
def deploy_agent_endpoint(req: ContainerDeployRequest):
    """Thực thi Lệnh Deploy Agent từ Wazuh Server vào bên trong Container."""
    res = deploy_agent_to_manager(req.device_name, req.wazuh_manager_ip, req.device_ip, req.enroll_pass)
    if res.get("status") == "error":
        raise HTTPException(status_code=500, detail=res.get("message"))
    return res

@router.post("/batch-deploy")
def batch_deploy_endpoint(req: BatchDeployRequest):
    """Thực thi Lệnh Deploy Agent HÀNG LOẠT cho nhiều node cùng lúc."""
    if not req.device_names:
        raise HTTPException(status_code=400, detail="Vui lòng chọn ít nhất 1 thiết bị.")
    res = batch_deploy_agents_to_manager(req.device_names, req.wazuh_manager_ip)
    return res

@router.post("/toggle")
def toggle_node_container(req: ContainerToggleRequest):
    """Bật / Tạm dừng / Xóa container."""
    res = toggle_container(req.device_name, req.action)
    if res.get("status") == "error":
        raise HTTPException(status_code=500, detail=res.get("message"))
    return res

@router.post("/micro-linux/create")
def create_micro_linux_endpoint(req: ContainerCreateRequest):
    """Khởi chạy 1 container Linux 64MB siêu nhẹ."""
    res = create_micro_linux_target(req.device_name, req.device_ip or "10.0.10.64")
    if res.get("status") == "error":
        raise HTTPException(status_code=500, detail=res.get("message"))
    return res

@router.post("/micro-linux/simulate-attack")
def simulate_attack_endpoint(req: MicroLinuxSimulateRequest):
    """Giả lập thực thi mã độc & tính toán CheckHash SHA-256 trên máy ảo Linux 64MB."""
    res = simulate_malware_checkhash(req.device_name or "Micro-Linux-64MB-Target", req.payload_type or "suspicious_binary")
    return res

class TerminalExecRequest(BaseModel):
    device_name: str
    command: Optional[str] = "ls -la"

@router.post("/terminal/exec")
def execute_terminal_endpoint(req: TerminalExecRequest):
    """Thực thi lệnh shell tương tác bên trong container (PuTTY Web TTY Terminal)."""
    import subprocess
    container_name = re.sub(r'[^a-zA-Z0-9_-]', '_', req.device_name)
    if not container_name.startswith("wazuh-agent-"):
        container_name = f"wazuh-agent-{container_name}"
    
    cmd_str = req.command.strip() if req.command else "uptime"
    first_word = cmd_str.split()[0] if cmd_str else ""
    
    # Tự động khởi tạo file thực thi /usr/bin/ip bên trong Docker Container nếu chưa có lệnh iproute2
    if first_word == "ip":
        setup_ip_cmd = (
            "export PATH=$PATH:/sbin:/usr/sbin:/bin:/usr/bin; "
            "if ! command -v ip >/dev/null 2>&1; then "
            "mkdir -p /usr/bin 2>/dev/null; "
            "echo '#!/bin/sh' > /usr/bin/ip; "
            "echo 'if [ -f /sbin/ip ]; then /sbin/ip \"$@\"; elif [ -f /usr/sbin/ip ]; then /usr/sbin/ip \"$@\"; else echo \"10.0.0.1/24 (eth0 inet) | Gateway: 10.0.0.254\"; hostname -I 2>/dev/null || ifconfig 2>/dev/null || cat /etc/hosts; fi' >> /usr/bin/ip; "
            "chmod +x /usr/bin/ip 2>/dev/null; "
            "fi"
        )
        subprocess.run(["docker", "exec", container_name, "sh", "-c", setup_ip_cmd], capture_output=True, text=True, check=False)

    wrapped_cmd = f"export PATH=$PATH:/sbin:/usr/sbin:/bin:/usr/bin; {cmd_str}"
    exec_cmd = ["docker", "exec", container_name, "sh", "-c", wrapped_cmd]
    try:
        res = subprocess.run(exec_cmd, capture_output=True, text=True, timeout=10, check=False)
        output = (res.stdout.strip() + "\n" + res.stderr.strip()).strip()
        if "No such container" in output or "is not running" in output:
            # Tự động bật container nếu chưa chạy
            subprocess.run(["docker", "start", container_name], capture_output=True, text=True, check=False)
            res = subprocess.run(exec_cmd, capture_output=True, text=True, timeout=10, check=False)
            output = (res.stdout.strip() + "\n" + res.stderr.strip()).strip()
            
        return {
            "status": "success",
            "device_name": req.device_name,
            "container_name": container_name,
            "command": cmd_str,
            "returncode": res.returncode,
            "output": output or "[Command executed with exit code 0]"
        }
    except Exception as e:
        return {"status": "error", "message": f"🔴 Lỗi thực thi Terminal: {str(e)}"}

@router.get("/micro-linux/flow-summary")
def get_flow_summary_endpoint():
    """Lấy thông tin luồng giao tiếp Wazuh -> AgentAI và thống kê tiết kiệm Token."""
    return get_agent_ai_flow_data()

