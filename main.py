from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from app.core.config import settings
from app.api.v1.router import api_router
from app.websockets.routes import router as ws_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Kích hoạt CORS (Rất quan trọng cho WebSockets và Frontend fetch API)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Trong production nên đặt đúng Domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Kết nối API v1 Logic
app.include_router(api_router, prefix=settings.API_V1_STR)

# Kết nối WebSocket Endpoints
app.include_router(ws_router)

# Phục vụ file Static (HTML, CSS, JS) để test giao diện
static_dir = os.path.join(os.path.dirname(__file__), "..", "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
def root():
    return {"message": "Hệ thống Online Exam Proctoring is running. Visit /static/proctor_dashboard.html"}
