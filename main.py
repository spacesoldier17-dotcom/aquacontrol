import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import asyncio
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base, AsyncSessionLocal
from routers import status, sensors, control, devices, events
import tasks
from models import Device
from sqlalchemy import select

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(status.router)
app.include_router(sensors.router)
app.include_router(control.router)
app.include_router(devices.router)
app.include_router(events.router)

app.mount("/static", StaticFiles(directory="static"), name="static")

async def init_default_devices():
    async with AsyncSessionLocal() as db:
        default_devices = [
            {"name": "Нагреватель", "type": "heater", "status": False, "power": 500.0, "mode": None},
            {"name": "Освещение", "type": "light", "status": False, "power": 50.0, "mode": "auto"},
            {"name": "Фильтр", "type": "filter", "status": False, "power": 100.0, "mode": None}
        ]
        for dev_data in default_devices:
            existing = await db.execute(select(Device).where(Device.name == dev_data["name"]))
            if not existing.scalar_one_or_none():
                db.add(Device(**dev_data))
        await db.commit()

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    await init_default_devices()
    asyncio.create_task(tasks.simulate_sensors())

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.get("/metrics")
async def metrics():
    return {"uptime": 12345, "version": "1.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)