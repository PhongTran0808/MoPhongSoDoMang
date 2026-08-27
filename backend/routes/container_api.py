from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from backend.services.container_service import (
    get_container_status,
    create_container,
    deploy_agent_to_manager,
    batch_deploy_agents_to_manager,
    toggle_container
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
