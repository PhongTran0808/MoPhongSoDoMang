import sys
import uvicorn
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from backend.routes.designer_api import router as designer_router
from backend.routes.injector_api import router as injector_router
from backend.routes.container_api import router as container_router

app = FastAPI(
    title="WazuhSim — Topology Designer & Log Injector",
    description="Lightweight Network Simulator & Syslog Generator for Wazuh Manager",
    version="1.0.0"
)

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"

# Mount static files
app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

# Include Routers
app.include_router(designer_router)
app.include_router(injector_router)
app.include_router(container_router)


@app.get("/", response_class=HTMLResponse)
def index_page():
    return FileResponse(str(FRONTEND_DIR / "index.html"))


if __name__ == "__main__":
    print("🚀 Starting WazuhSim Server on http://0.0.0.0:9090...")
    uvicorn.run("backend.main:app", host="0.0.0.0", port=9090, reload=True)
