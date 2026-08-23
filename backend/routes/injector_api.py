import threading
from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, Any, List
from backend.models.topology_models import ScenarioRequest
from backend.services.topology_store import load_topology
from backend.services.scenario_library import (
    get_available_scenarios, run_scenario_task, stop_current_scenario, SCENARIO_RUNNING_STATE
)

router = APIRouter(prefix="/api/injector", tags=["Log Injector & Scenario Engine"])


@router.get("/scenarios")
def list_scenarios():
    """Lấy danh sách các kịch bản tấn công có sẵn."""
    return get_available_scenarios()


@router.get("/status")
def get_status():
    """Lấy trạng thái thực thi kịch bản hiện tại."""
    return SCENARIO_RUNNING_STATE


@router.post("/run")
def trigger_scenario(req: ScenarioRequest, background_tasks: BackgroundTasks):
    """
    Kích hoạt chạy kịch bản giả lập tấn công.
    Tự động đọc IP thiết bị Nguồn và Đích từ topology.json!
    """
    if SCENARIO_RUNNING_STATE["is_running"]:
        raise HTTPException(status_code=400, detail="Một kịch bản đang chạy! Hãy bấm Dừng trước khi kích hoạt kịch bản mới.")

    topo = load_topology()
    src_dev = next((d for d in topo.devices if d.id == req.source_device_id), None)
    target_dev = next((d for d in topo.devices if d.id == req.target_device_id), None)

    if not src_dev:
        raise HTTPException(status_code=404, detail=f"Không tìm thấy thiết bị Nguồn (id={req.source_device_id})")
    if not target_dev:
        raise HTTPException(status_code=404, detail=f"Không tìm thấy thiết bị Đích (id={req.target_device_id})")

    # Run in background thread so HTTP response is immediate
    thread = threading.Thread(
        target=run_scenario_task,
        args=(req, src_dev, target_dev),
        daemon=True
    )
    thread.start()

    return {
        "status": "success",
        "message": f"Kích hoạt kịch bản {req.scenario_id} ({src_dev.name} [{src_dev.ip}] -> {target_dev.name} [{target_dev.ip}])",
        "target_wazuh": f"{req.wazuh_host}:{req.wazuh_syslog_port}"
    }


@router.post("/stop")
def stop_scenario():
    """Dừng kịch bản đang chạy."""
    stop_current_scenario()
    return {"status": "success", "message": "Đã gửi lệnh dừng kịch bản!"}
