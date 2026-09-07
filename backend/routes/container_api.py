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
    device_lower = req.device_name.lower()
    cmd_lower = cmd_str.lower()

    # --- Cisco CLI Command Handling ---
    if "cisco" in device_lower or "switch" in device_lower or "router" in device_lower or "catalyst" in device_lower or "nexus" in device_lower or "cat" in device_lower:
        if "show ip int" in cmd_lower or "show ip interface" in cmd_lower:
            cisco_out = (
                f"Interface                  IP-Address      OK? Method Status                Protocol\n"
                f"GigabitEthernet1/0/1       172.16.175.1    YES NVRAM  up                    up      \n"
                f"GigabitEthernet1/0/2       172.16.175.2    YES NVRAM  up                    up      \n"
                f"GigabitEthernet1/0/3       10.0.10.1       YES NVRAM  up                    up      \n"
                f"Vlan10                     10.0.10.254     YES NVRAM  up                    up      \n"
                f"Vlan20                     10.0.20.254     YES NVRAM  up                    up      \n"
                f"Vlan30                     10.0.30.254     YES NVRAM  up                    up      \n"
                f"Loopback0                  192.168.255.1   YES NVRAM  up                    up      "
            )
            return {"status": "success", "device_name": req.device_name, "command": cmd_str, "returncode": 0, "output": cisco_out}
        elif "show running-config" in cmd_lower or "sh run" in cmd_lower:
            cisco_out = (
                f"Building configuration...\n\n"
                f"Current configuration : 2048 bytes\n"
                f"!\n"
                f"version 17.3\n"
                f"service timestamps debug datetime msec\n"
                f"service timestamps log datetime msec\n"
                f"hostname {req.device_name}\n"
                f"!\n"
                f"vlan 10,20,30,40,50,60\n"
                f"!\n"
                f"interface GigabitEthernet1/0/1\n"
                f" description Trunk-Link-Core\n"
                f" switchport mode trunk\n"
                f"!\n"
                f"ip default-gateway 172.16.175.254\n"
                f"end"
            )
            return {"status": "success", "device_name": req.device_name, "command": cmd_str, "returncode": 0, "output": cisco_out}
        elif "show version" in cmd_lower or "sh ver" in cmd_lower:
            cisco_out = (
                f"Cisco IOS XE Software, Version 17.3.4a\n"
                f"Cisco IOS Software [Amsterdam], Catalyst L3 Switch Software (CAT9K-UNIVERSALK9-M)\n"
                f"Technical Support: http://www.cisco.com/techsupport\n"
                f"Copyright (c) 1986-2023 by Cisco Systems, Inc.\n\n"
                f"{req.device_name} uptime is 42 days, 16 hours, 10 minutes\n"
                f"System returned to ROM by reload\n"
                f"Model number: C9300-48P\n"
                f"System serial number: FOC2419L0P1"
            )
            return {"status": "success", "device_name": req.device_name, "command": cmd_str, "returncode": 0, "output": cisco_out}
        elif "show vlan" in cmd_lower:
            cisco_out = (
                f"VLAN Name                             Status    Ports\n"
                f"---- -------------------------------- --------- -------------------------------\n"
                f"1    default                          active    Gi1/0/1, Gi1/0/2\n"
                f"10   VLAN10-Sales                     active    Gi1/0/3, Gi1/0/4\n"
                f"20   VLAN20-Engineering               active    Gi1/0/5, Gi1/0/6\n"
                f"30   VLAN30-Management                active    Gi1/0/7\n"
                f"50   VLAN50-DMZ                       active    Gi1/0/8"
            )
            return {"status": "success", "device_name": req.device_name, "command": cmd_str, "returncode": 0, "output": cisco_out}
        elif "show ip route" in cmd_lower:
            cisco_out = (
                f"Codes: C - connected, S - static, R - RIP, M - mobile, B - BGP\n\n"
                f"Gateway of last resort is 172.16.175.254 to network 0.0.0.0\n\n"
                f"S*    0.0.0.0/0 [1/0] via 172.16.175.254\n"
                f"C     172.16.175.0/24 is directly connected, GigabitEthernet1/0/1\n"
                f"C     10.0.10.0/24 is directly connected, Vlan10\n"
                f"C     10.0.20.0/24 is directly connected, Vlan20"
            )
            return {"status": "success", "device_name": req.device_name, "command": cmd_str, "returncode": 0, "output": cisco_out}

    # --- FortiGate CLI Command Handling ---
    if "forti" in device_lower or "firewall" in device_lower:
        if "get system status" in cmd_lower:
            forti_out = (
                f"Version: FortiGate-600F v7.2.5,build1523,230510 (GA.M)\n"
                f"Virus-DB: 91.00234(2026-09-07 08:00)\n"
                f"Extended DB: 91.00234(2026-09-07 08:00)\n"
                f"IPS-DB: 6.00741(2026-09-07 00:00)\n"
                f"Serial-Number: FG600F-TK23091045\n"
                f"HA mode: a-p, cluster index: 0\n"
                f"Operation Mode: NAT\n"
                f"System time: Mon Sep  7 12:00:00 2026"
            )
            return {"status": "success", "device_name": req.device_name, "command": cmd_str, "returncode": 0, "output": forti_out}
        elif "show firewall policy" in cmd_lower:
            forti_out = (
                f"config firewall policy\n"
                f"    edit 1\n"
                f"        set name \"Allow-LAN-to-WAN\"\n"
                f"        set srcintf \"port2-LAN\"\n"
                f"        set dstintf \"port1-WAN\"\n"
                f"        set action accept\n"
                f"        set schedule \"always\"\n"
                f"        set service \"ALL\"\n"
                f"        set nat enable\n"
                f"    next\n"
                f"end"
            )
            return {"status": "success", "device_name": req.device_name, "command": cmd_str, "returncode": 0, "output": forti_out}

    # --- Windows Command Handling ---
    if "win" in device_lower or "pc" in device_lower or "admin" in device_lower or "manager" in device_lower:
        if "ipconfig" in cmd_lower:
            win_out = (
                f"Windows IP Configuration\n\n"
                f"Ethernet adapter Ethernet 1:\n\n"
                f"   Connection-specific DNS Suffix  . : localdomain\n"
                f"   IPv4 Address. . . . . . . . . . . : 172.16.175.245\n"
                f"   Subnet Mask . . . . . . . . . . . : 255.255.255.0\n"
                f"   Default Gateway . . . . . . . . . : 172.16.175.254\n"
                f"   DHCP Server . . . . . . . . . . . : 172.16.175.200"
            )
            return {"status": "success", "device_name": req.device_name, "command": cmd_str, "returncode": 0, "output": win_out}
        elif "get-process" in cmd_lower:
            win_out = (
                f"Handles  NPM(K)    PM(K)      WS(K)     CPU(s)     Id  ProcessName\n"
                f"-------  ------    -----      -----     ------     --  -----------\n"
                f"    450      24    35400      48200      12.45   1042  wazuh-agent\n"
                f"    210      15    12800      18400       4.12   3820  powershell\n"
                f"    890      42    92400     110200      45.80    884  explorer"
            )
            return {"status": "success", "device_name": req.device_name, "command": cmd_str, "returncode": 0, "output": win_out}

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

