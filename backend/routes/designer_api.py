from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List
from backend.models.topology_models import TopologyData, DeviceModel, LinkModel
from backend.services.topology_store import load_topology, save_topology, export_to_agent_wazuh

router = APIRouter(prefix="/api/topology", tags=["Topology Designer"])


@router.get("", response_model=TopologyData)
def get_topology():
    """Lấy sơ đồ mạng hiện tại."""
    return load_topology()


@router.post("/save")
def update_full_topology(topo: TopologyData):
    """Lưu toàn bộ sơ đồ mạng."""
    topo.last_updated = str(topo.last_updated or "Just now")
    if save_topology(topo):
        return {"status": "success", "message": "Đã lưu sơ đồ thành công!"}
    raise HTTPException(status_code=500, detail="Không thể lưu topology.json")


@router.post("/device")
def add_or_update_device(dev: DeviceModel):
    """Thêm hoặc cập nhật một thiết bị."""
    topo = load_topology()
    existing_idx = next((i for i, d in enumerate(topo.devices) if d.id == dev.id), None)
    if existing_idx is not None:
        topo.devices[existing_idx] = dev
    else:
        topo.devices.append(dev)
    
    if save_topology(topo):
        return {"status": "success", "device": dev}
    raise HTTPException(status_code=500, detail="Không thể lưu thiết bị")


@router.delete("/device/{device_id}")
def delete_device(device_id: str):
    """Xóa một thiết bị và các link liên quan."""
    topo = load_topology()
    topo.devices = [d for d in topo.devices if d.id != device_id]
    topo.links = [l for l in topo.links if l.from_id != device_id and l.to_id != device_id]
    
    if save_topology(topo):
        return {"status": "success", "deleted_id": device_id}
    raise HTTPException(status_code=500, detail="Không thể xóa thiết bị")


@router.post("/link")
def add_link(link: LinkModel):
    """Tạo liên kết giữa 2 thiết bị."""
    topo = load_topology()
    # Remove existing link if same id
    topo.links = [l for l in topo.links if l.id != link.id]
    topo.links.append(link)
    
    if save_topology(topo):
        return {"status": "success", "link": link}
    raise HTTPException(status_code=500, detail="Không thể lưu liên kết")


@router.delete("/link/{link_id}")
def delete_link(link_id: str):
    """Xóa liên kết."""
    topo = load_topology()
    topo.links = [l for l in topo.links if l.id != link_id]
    if save_topology(topo):
        return {"status": "success", "deleted_link_id": link_id}
    raise HTTPException(status_code=500, detail="Không thể xóa liên kết")


@router.post("/export-agent-wazuh")
def export_to_agentwazuh():
    """1-Click Export: Đồng bộ danh sách thiết bị sang config/known_devices.json của AgentWazuh."""
    result = export_to_agent_wazuh()
    if result.get("status") == "success":
        return result
    raise HTTPException(status_code=500, detail=result.get("message", "Lỗi export"))
