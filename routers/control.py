from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import get_db
from models import Device
import crud, schemas
from dependencies import send_notification

router = APIRouter(prefix="/api/v1/control", tags=["control"])

class TemperatureTarget(BaseModel):
    target: float

class FeedingPortion(BaseModel):
    portion: float

class LightMode(BaseModel):
    mode: str

@router.post("/temperature")
async def set_temperature(target: TemperatureTarget, db: AsyncSession = Depends(get_db)):
    heater = await db.execute(select(Device).where(Device.name == "Нагреватель"))
    heater = heater.scalar_one_or_none()
    if not heater:
        raise HTTPException(status_code=404, detail="Heater not found")
    new_status = True if target.target > 25 else False
    old_status = heater.status
    heater.status = new_status
    await db.commit()
    event1 = schemas.EventCreate(event_type="info", source="user", description=f"Установлена целевая температура {target.target}°C", priority=2)
    await crud.create_event(db, event1)
    if old_status != new_status:
        event2 = schemas.EventCreate(event_type="info", source="system", description=f"Нагреватель {'включен' if new_status else 'выключен'} (целевая температура {target.target}°C)", priority=2)
        await crud.create_event(db, event2)
    return {"status": "ok", "target": target.target, "heater_on": new_status}

@router.post("/feeding")
async def feed(portion: FeedingPortion, db: AsyncSession = Depends(get_db)):
    event = schemas.EventCreate(event_type="info", source="user", description=f"Ручное кормление порцией {portion.portion}", priority=2)
    await crud.create_event(db, event)
    await send_notification("feeding", f"Выполнено кормление порцией {portion.portion}")
    return {"status": "feeding triggered"}

@router.post("/light/mode")
async def set_light_mode(mode_data: LightMode, db: AsyncSession = Depends(get_db)):
    light = await db.execute(select(Device).where(Device.name == "Освещение"))
    light = light.scalar_one_or_none()
    if not light:
        raise HTTPException(status_code=404, detail="Light not found")
    old_mode = light.mode
    light.mode = mode_data.mode
    if mode_data.mode == "day":
        light.status = True
    elif mode_data.mode == "night":
        light.status = False
    elif mode_data.mode == "auto":
        pass  # статус определится позже
    else:
        raise HTTPException(status_code=400, detail="Mode must be 'day', 'night' or 'auto'")
    await db.commit()
    event = schemas.EventCreate(event_type="info", source="user", description=f"Режим освещения изменён с '{old_mode}' на '{mode_data.mode}'", priority=2)
    await crud.create_event(db, event)
    return {"status": "ok", "mode": mode_data.mode, "light_status": light.status}