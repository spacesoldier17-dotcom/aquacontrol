from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import get_db
from models import Device
from schemas import DeviceCreate
import crud, schemas

router = APIRouter(prefix="/api/v1/devices", tags=["devices"])

@router.get("/")
async def list_devices(db: AsyncSession = Depends(get_db)):
    devices = await crud.get_all_devices(db)
    return devices

@router.put("/{device_id}")
async def update_device(device_id: int, device_data: DeviceCreate, db: AsyncSession = Depends(get_db)):
    device = await db.get(Device, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    old_status = device.status
    old_power = device.power
    old_mode = device.mode
    
    device.name = device_data.name
    device.type = device_data.type
    device.status = device_data.status
    device.power = device_data.power
    device.mode = device_data.mode
    await db.commit()
    
    changes = []
    if old_status != device.status:
        changes.append(f"статус: {old_status}→{device.status}")
    if old_power != device.power:
        changes.append(f"мощность: {old_power}→{device.power}")
    if old_mode != device.mode:
        changes.append(f"режим: {old_mode}→{device.mode}")
    if device.name != device_data.name:
        changes.append(f"имя: {device.name}")
    if device.type != device_data.type:
        changes.append(f"тип: {device.type}")
    
    desc = f"Обновлено устройство id={device_id}: " + (", ".join(changes) if changes else "без изменений")
    event = schemas.EventCreate(event_type="info", source="user", description=desc, priority=2)
    await crud.create_event(db, event)
    return device

@router.post("/{device_id}/toggle")
async def toggle_device(device_id: int, db: AsyncSession = Depends(get_db)):
    device = await db.get(Device, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    old_status = device.status
    device.status = not device.status
    await db.commit()
    event = schemas.EventCreate(
        event_type="info",
        source="user",
        description=f"Устройство '{device.name}' (id={device_id}) {'включено' if device.status else 'выключено'}",
        priority=2
    )
    await crud.create_event(db, event)
    return {"id": device.id, "name": device.name, "status": device.status, "power": device.power, "mode": device.mode}

@router.post("/{device_id}/set_power")
async def set_device_power(device_id: int, power: float, db: AsyncSession = Depends(get_db)):
    device = await db.get(Device, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    old_power = device.power
    device.power = power
    await db.commit()
    event = schemas.EventCreate(
        event_type="info",
        source="user",
        description=f"Мощность устройства '{device.name}' (id={device_id}) изменена с {old_power} на {power}",
        priority=2
    )
    await crud.create_event(db, event)
    return {"id": device.id, "name": device.name, "power": device.power, "status": device.status, "mode": device.mode}

@router.post("/{device_id}/set_mode")
async def set_device_mode(device_id: int, mode: str, db: AsyncSession = Depends(get_db)):
    device = await db.get(Device, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    old_mode = device.mode
    device.mode = mode
    await db.commit()
    event = schemas.EventCreate(
        event_type="info",
        source="user",
        description=f"Режим устройства '{device.name}' (id={device_id}) изменён с '{old_mode}' на '{mode}'",
        priority=2
    )
    await crud.create_event(db, event)
    return {"id": device.id, "name": device.name, "mode": device.mode, "status": device.status, "power": device.power}