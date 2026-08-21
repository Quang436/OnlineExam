from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from app.api.v1.router import api_v1_router
from app.websockets.routes import ws_router
from app.core.config import settings
from app.core.database import Base, engine
import app.models

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Khởi tạo tables chuẩn khi bật hệ thống
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    lifespan=lifespan,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# REST API & WebSockets Router
app.include_router(api_v1_router, prefix=settings.API_V1_STR)
app.include_router(ws_router)

# === Phục hồi Mount Đường dẫn HTML tĩnh của bạn ===
static_dir = os.path.join(os.path.dirname(__file__), "..", "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
async def root():
    return {"message": "Hệ thống đã phục hồi trọn vẹn! Vào /static/proctor_dashboard.html để Test."}