import socket
import time
import datetime
import random
import logging
from typing import Dict, Any, List, Optional
from backend.models.topology_models import DeviceModel

logger = logging.getLogger("LogInjector")


class LogInjector:
    """
    Service sinh & gửi log UDP Syslog THẬT tới Wazuh Manager (Port 514 UDP).
    Log được định dạng khớp 100% với chuẩn Syslog của FortiGate, Windows Event, Cisco, Linux.
    Wazuh Manager thật sẽ tự động parse qua decoders/rules thật và sinh Alert thật!
    """

    def __init__(self, wazuh_host: str = "172.16.175.145", wazuh_port: int = 514):
        self.wazuh_host = wazuh_host
        self.wazuh_port = wazuh_port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def send_raw_syslog(self, syslog_msg: str) -> bool:
        """Gửi 1 chuỗi log UDP tới Wazuh Manager."""
        try:
            payload = syslog_msg.encode('utf-8')
            self.sock.sendto(payload, (self.wazuh_host, self.wazuh_port))
            return True
        except Exception as e:
            logger.error(f"Failed to send UDP syslog to {self.wazuh_host}:{self.wazuh_port}: {e}")
            return False

    def generate_ssh_brute_force_log(self, src_device: DeviceModel, target_device: DeviceModel, success: bool = False) -> str:
        """
        Sinh log SSH Password Failure / Success cho Linux Server.
        Format chuẩn RFC3164 Syslog:
        <13>Aug 23 13:30:00 target_name sshd[1234]: Failed password for invalid user admin from src_ip port 54321 ssh2
        """
        now = datetime.datetime.now().strftime("%b %d %H:%M:%S")
        pid = random.randint(1000, 9999)
        src_port = random.randint(30000, 60000)
        
        if success:
            return f"<13>{now} {target_device.name} sshd[{pid}]: Accepted password for root from {src_device.ip} port {src_port} ssh2"
        else:
            invalid_users = ["admin", "root", "oracle", "postgres", "guest", "ubuntu", "test"]
            user = random.choice(invalid_users)
            return f"<13>{now} {target_device.name} sshd[{pid}]: Failed password for invalid user {user} from {src_device.ip} port {src_port} ssh2"

    def generate_fortigate_firewall_log(self, src_device: DeviceModel, target_device: DeviceModel, action: str = "deny") -> str:
        """
        Sinh log FortiGate Syslog format chuẩn (CEF / Key-Value format).
        Wazuh ruleset có sẵn fortigate decoder.
        """
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        session_id = random.randint(100000, 999999)
        src_port = random.randint(1024, 65535)
        dst_port = random.choice([22, 80, 443, 3389, 445, 8080, 21])
        
        return (
            f"<134>date={now.split()[0]} time={now.split()[1]} devname=\"{src_device.name}\" "
            f"devid=\"FGT60E-SIMULATED\" logid=\"0000000013\" type=\"traffic\" subtype=\"forward\" "
            f"level=\"warning\" vd=\"root\" srcip={src_device.ip} srcport={src_port} "
            f"dstip={target_device.ip} dstport={dst_port} sessionid={session_id} "
            f"action=\"{action}\" policyid=1 dstcountry=\"Internal\" srccountry=\"Internal\" "
            f"trandisp=\"noop\" service=\"TCP/{dst_port}\" app=\"HTTP\" duration=1 sentbyte=60 rcvdbyte=0"
        )

    def generate_windows_event_log(self, src_device: DeviceModel, target_device: DeviceModel, event_id: int = 4625) -> str:
        """
        Sinh log Windows Event Log 4625 (Failed Logon) hoặc 4624 (Successful Logon).
        Format MSWinEventLog cho Wazuh Windows decoder.
        """
        now = datetime.datetime.now().strftime("%b %d %H:%M:%S")
        user = random.choice(["Administrator", "SYSTEM", "sql_svc", "domain_admin"])
        
        if event_id == 4625:
            # Failed Logon
            return (
                f"<13>{now} {target_device.name} WinEvtLog: Security: AUDIT_FAILURE({event_id}): "
                f"Microsoft-Windows-Security-Auditing: {user}: DOMAIN: {target_device.name}: "
                f"An account failed to log on. Subject: Security ID: S-1-0-0 Account Name: - "
                f"Target Account: Account Name: {user} Account Domain: DOMAIN "
                f"Failure Information: Failure Reason: Unknown user name or bad password. "
                f"Status: 0xc000006d Sub Status: 0xc000006a "
                f"Process Information: Caller Process ID: 0x44c "
                f"Network Information: Workstation Name: {src_device.name} Source Network Address: {src_device.ip} Source Port: 49152"
            )
        else:
            # Successful Logon
            return (
                f"<13>{now} {target_device.name} WinEvtLog: Security: AUDIT_SUCCESS({event_id}): "
                f"Microsoft-Windows-Security-Auditing: {user}: DOMAIN: {target_device.name}: "
                f"An account was successfully logged on. "
                f"Target Account: Account Name: {user} Account Domain: DOMAIN "
                f"Logon Type: 10 Source Network Address: {src_device.ip}"
            )

    def generate_ransomware_log(self, src_device: DeviceModel, target_device: DeviceModel) -> str:
        """
        Sinh chuỗi log giả lập ransomware đổi tên hàng loạt file .encrypted & mod registry.
        """
        now = datetime.datetime.now().strftime("%b %d %H:%M:%S")
        ext = random.choice([".locked", ".crypto", ".ransom", ".enc"])
        file_path = f"C:\\Users\\Public\\Documents\\financial_data_{random.randint(100,999)}{ext}"
        
        return (
            f"<13>{now} {target_device.name} WinEvtLog: Security: AUDIT_FAILURE(4663): "
            f"Microsoft-Windows-Security-Auditing: SYSTEM: DOMAIN: {target_device.name}: "
            f"An attempt was made to access an object. Object Name: {file_path} "
            f"Process Name: C:\\Users\\Public\\svchost_update.exe Accesses: WriteData Delete"
        )
