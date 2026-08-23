from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field


class DeviceModel(BaseModel):
    id: str = Field(description="Unique device identifier e.g. dev_1")
    name: str = Field(description="Display name e.g. FortiGate-Core")
    ip: str = Field(description="Primary IP address e.g. 172.16.175.200")
    secondary_ip: Optional[str] = None
    type: Literal["firewall", "router", "switch", "server", "endpoint", "pc", "cloud", "internet", "unknown"] = "server"
    os: str = "Linux"
    criticality: int = Field(default=5, ge=1, le=10)
    syslog_format: str = Field(default="auto", description="auto | cef | winevent | cisco | syslog")
    x: float = 0.0
    y: float = 0.0
    verified: bool = True
    open_ports: List[int] = Field(default_factory=lambda: [22, 80, 443])
    ha_group: Optional[str] = None
    vpn_tunnel: Optional[str] = None


class LinkModel(BaseModel):
    id: str
    from_id: str
    to_id: str
    label: str = ""
    bandwidth: str = "1G"
    link_type: Literal["ethernet", "vpn", "sdwan", "ha"] = "ethernet"


class HAGroupModel(BaseModel):
    id: str
    name: str
    primary_device_id: str
    secondary_device_id: str
    mode: Literal["active-passive", "active-active"] = "active-passive"


class VPNTunnelModel(BaseModel):
    id: str
    name: str
    source_device_id: str
    target_device_id: str
    tunnel_type: str = "IPsec"
    status: str = "up"


class TopologyData(BaseModel):
    devices: List[DeviceModel] = Field(default_factory=list)
    links: List[LinkModel] = Field(default_factory=list)
    ha_groups: List[HAGroupModel] = Field(default_factory=list)
    vpn_tunnels: List[VPNTunnelModel] = Field(default_factory=list)
    last_updated: Optional[str] = None


class ScenarioRequest(BaseModel):
    scenario_id: str
    source_device_id: str
    target_device_id: str
    wazuh_host: str = "172.16.175.145"
    wazuh_syslog_port: int = 514
    burst_count: int = 30
