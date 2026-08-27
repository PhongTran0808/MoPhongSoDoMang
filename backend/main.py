import sys
import uvicorn
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from fastapi import FastAPI, Request
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

# Anti-cache middleware for static assets & JS
@app.middleware("http")
async def add_anti_cache_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    return response

# Base directories
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

# Fallback for root static requests (e.g. /style.css, /js/...)
@app.get("/{filepath:path}")
def serve_root_static(filepath: str):
    target = FRONTEND_DIR / filepath
    if target.exists() and target.is_file():
        return FileResponse(str(target))
    return HTMLResponse("Not Found", status_code=404)

if __name__ == "__main__":
    print("🚀 Starting WazuhSim Server on http://0.0.0.0:9090...")
    uvicorn.run("backend.main:app", host="0.0.0.0", port=9090, reload=False)
