import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from backend.models.topology_models import TopologyData, DeviceModel

logger = logging.getLogger("TopologyStore")

# Default path for topology.json inside WazuhSim
TOPOLOGY_FILE = Path(__file__).resolve().parent.parent.parent / "config" / "topology.json"

# AgentWazuh path for 1-click export
AGENT_WAZUH_KNOWN_DEVICES = Path("/run/media/kweismann/Dir_D/Tiểu luận CN/AgentWazuh/config/known_devices.json")


def load_topology() -> TopologyData:
    """Load topology from topology.json file."""
    if not TOPOLOGY_FILE.exists():
        TOPOLOGY_FILE.parent.mkdir(parents=True, exist_ok=True)
        default_topo = TopologyData(
            devices=[
                DeviceModel(id="dev_fw1", name="FortiGate-Core", ip="172.16.175.200", type="firewall", os="FortiOS 7.2", criticality=9, x=-200, y=0),
                DeviceModel(id="dev_r1", name="Cisco-Gateway", ip="172.16.175.201", type="router", os="Cisco IOS-XE", criticality=8, x=0, y=-150),
                DeviceModel(id="dev_sw1", name="Access-Switch-01", ip="172.16.175.202", type="switch", os="Cisco Nexus", criticality=6, x=0, y=150),
                DeviceModel(id="dev_srv1", name="App-Server-Ubuntu", ip="172.16.175.210", type="server", os="Ubuntu 22.04 LTS", criticality=9, x=200, y=-100),
                DeviceModel(id="dev_pc1", name="User-PC-Win11", ip="172.16.175.220", type="pc", os="Windows 11 Enterprise", criticality=4, x=200, y=100)
            ],
            links=[]
        )
        save_topology(default_topo)
        return default_topo

    try:
        data = json.loads(TOPOLOGY_FILE.read_text(encoding="utf-8"))
        return TopologyData(**data)
    except Exception as e:
        logger.error(f"Failed to load topology.json: {e}")
        return TopologyData()


def save_topology(topo: TopologyData) -> bool:
    """Save topology to topology.json atomically to prevent partial/truncated writes."""
    try:
        TOPOLOGY_FILE.parent.mkdir(parents=True, exist_ok=True)
        tmp_file = TOPOLOGY_FILE.with_suffix(".json.tmp")
        tmp_file.write_text(topo.model_dump_json(indent=2), encoding="utf-8")
        tmp_file.replace(TOPOLOGY_FILE)
        logger.info(f"Successfully saved topology to {TOPOLOGY_FILE}")
        return True
    except Exception as e:
        logger.error(f"Failed to save topology.json: {e}")
        return False


def export_to_agent_wazuh() -> Dict[str, Any]:
    """
    Export current topology devices to AgentWazuh's config/known_devices.json.
    This links WazuhSim topology to AgentWazuh's correlation engine!
    """
    topo = load_topology()
    exported_list = []
    
    for dev in topo.devices:
        exported_list.append({
            "ip": dev.ip,
            "name": dev.name,
            "type": dev.type.upper(),
            "criticality": dev.criticality,
            "verified": dev.verified,
            "status": "up",
            "os": dev.os
        })

    # Add Wazuh Server entry if missing
    wazuh_server_ip = "172.16.175.145"
    if not any(d["ip"] == wazuh_server_ip for d in exported_list):
        exported_list.insert(0, {
            "ip": wazuh_server_ip,
            "name": "Wazuh Server",
            "type": "SIEM",
            "criticality": 10,
            "verified": True,
            "status": "up",
            "os": "Amazon Linux 2023 (Wazuh Manager)"
        })

    try:
        AGENT_WAZUH_KNOWN_DEVICES.parent.mkdir(parents=True, exist_ok=True)
        AGENT_WAZUH_KNOWN_DEVICES.write_text(json.dumps(exported_list, indent=2, ensure_ascii=False), encoding="utf-8")
        logger.info(f"Exported {len(exported_list)} devices to AgentWazuh: {AGENT_WAZUH_KNOWN_DEVICES}")
        return {"status": "success", "count": len(exported_list), "target": str(AGENT_WAZUH_KNOWN_DEVICES)}
    except Exception as e:
        logger.error(f"Failed to export to AgentWazuh: {e}")
        return {"status": "error", "message": str(e)}
