from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from backend.services.container_service import (
    get_container_status,
    create_container,
    toggle_container,
    batch_create_all_containers
)

router = APIRouter(prefix="/api/container", tags=["Container Manager"])

class ContainerCreateRequest(BaseModel):
    device_name: str
    wazuh_manager_ip: Optional[str] = "172.16.175.145"
    device_ip: Optional[str] = None
    enroll_pass: Optional[str] = None

class ContainerBatchCreateRequest(BaseModel):
    wazuh_manager_ip: Optional[str] = "172.16.175.145"
    enroll_pass: Optional[str] = None

class ContainerToggleRequest(BaseModel):
    device_name: str
    action: str  # "start", "stop", "remove"

@router.get("/status/{device_name:path}")
def check_status(device_name: str):
    """Lấy trạng thái Docker container của 1 thiết bị."""
    return get_container_status(device_name)

@router.post("/create")
def create_node_container(req: ContainerCreateRequest):
    """Khởi tạo container mới cho 1 node."""
    res = create_container(req.device_name, req.wazuh_manager_ip, req.device_ip, req.enroll_pass)
    if res.get("status") == "error":
        raise HTTPException(status_code=500, detail=res.get("message"))
    return res

@router.post("/batch-create")
def batch_create_nodes(req: ContainerBatchCreateRequest):
    """Tạo toàn bộ container cho tất cả các node trong sơ đồ."""
    res = batch_create_all_containers(req.wazuh_manager_ip, req.enroll_pass)
    if res.get("status") == "error":
        raise HTTPException(status_code=500, detail=res.get("message"))
    return res

@router.post("/toggle")
def toggle_node_container(req: ContainerToggleRequest):
    """Bật / Tạm dừng / Xóa container."""
    res = toggle_container(req.device_name, req.action)
    if res.get("status") == "error":
        raise HTTPException(status_code=500, detail=res.get("message"))
    return res
