import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from backend.app.config import get_settings
from backend.app.database import engine
from backend.app.models import Base
from backend.app.routes import auth, violations, review, analytics, cameras, health, catalog
from backend.app.services.elasticsearch import es_service

settings = get_settings()
limiter = Limiter(key_func=get_remote_address)


async def seed_database():
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy import select
    from backend.app.database import AsyncSessionLocal
    from backend.app.models import Role, Permission, User, Camera, ThresholdConfig, CameraStatus
    from backend.app.auth import get_password_hash

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        existing = await db.execute(select(Role).limit(1))
        if existing.scalar_one_or_none():
            return

        roles = [
            Role(name="Admin", description="Full system access"),
            Role(name="Supervisor", description="Review and manage officers"),
            Role(name="Officer", description="Review violations"),
            Role(name="Analyst", description="Analytics and reporting"),
        ]
        for role in roles:
            db.add(role)
        await db.flush()

        admin_role = roles[0]
        admin = User(
            email="admin@trafficguard.ai",
            hashed_password=get_password_hash("admin123"),
            full_name="System Administrator",
            role_id=admin_role.id,
            is_verified=True,
        )
        db.add(admin)

        demo_cameras = [
            Camera(name="MG Road Junction", camera_id="CAM-001", stream_url="rtsp://demo/cam1",
                   latitude=12.9716, longitude=77.5946, location_name="MG Road, Bangalore", status=CameraStatus.ONLINE),
            Camera(name="Indiranagar Signal", camera_id="CAM-002", stream_url="rtsp://demo/cam2",
                   latitude=12.9784, longitude=77.6408, location_name="Indiranagar, Bangalore", status=CameraStatus.ONLINE),
            Camera(name="Electronic City Gate", camera_id="CAM-003", stream_url="rtsp://demo/cam3",
                   latitude=12.8456, longitude=77.6603, location_name="Electronic City, Bangalore", status=CameraStatus.ONLINE),
            Camera(name="Whitefield Hub", camera_id="CAM-004", stream_url="rtsp://demo/cam4",
                   latitude=12.9698, longitude=77.7500, location_name="Whitefield, Bangalore", status=CameraStatus.OFFLINE),
        ]
        for cam in demo_cameras:
            db.add(cam)

        db.add(ThresholdConfig(name="default", auto_process_threshold=0.85, human_review_threshold=0.60))
        await db.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await seed_database()
    try:
        await es_service.connect()
    except Exception:
        pass
    yield
    await es_service.close()


app = FastAPI(
    title=settings.app_name,
    description="Uncertainty-Aware Traffic Violation Detection Platform",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

prefix = settings.api_v1_prefix
app.include_router(auth.router, prefix=prefix)
app.include_router(violations.router, prefix=prefix)
app.include_router(review.router, prefix=prefix)
app.include_router(analytics.router, prefix=prefix)
app.include_router(cameras.router, prefix=prefix)
app.include_router(health.router, prefix=prefix)
app.include_router(catalog.router, prefix=prefix)


@app.get("/")
async def root():
    return {
        "name": settings.app_name,
        "tagline": "Confident Enforcement. Humble Flagging.",
        "version": "1.0.0",
        "docs": "/docs",
    }
