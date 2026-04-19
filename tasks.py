import asyncio
import random
from datetime import datetime
from database import AsyncSessionLocal
from sqlalchemy import select
import crud, schemas
from models import Device

BASE_RANGES = {
    'temperature': (20.0, 30.0),
    'ph': (6.5, 8.5),
    'ammonia': (0.0, 2.0),
    'oxygen': (4.0, 8.0),
    'turbidity': (0.0, 10.0)
}

DEVICE_EFFECTS = {
    'heater': {'temperature': (+0.5, 2.0)},
    'light': {'oxygen': (+0.2, 1.0), 'turbidity': (-0.5, 2.0)},
    'filter': {'ammonia': (-0.3, 1.5), 'turbidity': (-0.4, 1.5)}
}

async def get_device(db, name):
    result = await db.execute(select(Device).where(Device.name == name))
    return result.scalar_one_or_none()

def is_light_on_by_mode(mode, current_hour=None):
    if mode == "day":
        return True
    elif mode == "night":
        return False
    elif mode == "auto":
        if current_hour is None:
            current_hour = datetime.now().hour
        return 8 <= current_hour < 20
    return False

async def simulate_sensors():
    while True:
        await asyncio.sleep(5)
        async with AsyncSessionLocal() as db:
            heater = await get_device(db, "Нагреватель")
            light = await get_device(db, "Освещение")
            filter_dev = await get_device(db, "Фильтр")
            heater_on = heater.status if heater else False
            filter_on = filter_dev.status if filter_dev else False
            if light:
                current_hour = datetime.now().hour
                light_on = is_light_on_by_mode(light.mode, current_hour)
                if light.status != light_on:
                    light.status = light_on
                    await db.commit()
            else:
                light_on = False
            sensors_data = {}
            for stype, (low, high) in BASE_RANGES.items():
                value = random.uniform(low, high)
                if heater_on and stype in DEVICE_EFFECTS.get('heater', {}):
                    delta, max_delta = DEVICE_EFFECTS['heater'][stype]
                    value += random.uniform(0, max_delta) * (1 if delta>0 else -1)
                if light_on and stype in DEVICE_EFFECTS.get('light', {}):
                    delta, max_delta = DEVICE_EFFECTS['light'][stype]
                    value += random.uniform(0, max_delta) * (1 if delta>0 else -1)
                if filter_on and stype in DEVICE_EFFECTS.get('filter', {}):
                    delta, max_delta = DEVICE_EFFECTS['filter'][stype]
                    value += random.uniform(0, max_delta) * (1 if delta>0 else -1)
                # Ограничения
                if stype == 'temperature':
                    value = max(15.0, min(35.0, value))
                elif stype == 'ph':
                    value = max(6.0, min(9.0, value))
                elif stype == 'ammonia':
                    value = max(0.0, min(3.0, value))
                elif stype == 'oxygen':
                    value = max(3.0, min(10.0, value))
                elif stype == 'turbidity':
                    value = max(0.0, min(20.0, value))
                sensors_data[stype] = round(value, 2)
            units = {'temperature': '°C', 'ph': 'pH', 'ammonia': 'mg/L', 'oxygen': 'mg/L', 'turbidity': 'NTU'}
            for stype, value in sensors_data.items():
                reading = schemas.SensorReadingCreate(sensor_type=stype, value=value, unit=units[stype])
                await crud.create_sensor_reading(db, reading)
                low, high = BASE_RANGES[stype]
                if value < low * 0.8 or value > high * 1.2:
                    desc = f"⚠️ Аномалия {stype}: {value}{units[stype]} (норма {low}-{high})"
                    event = schemas.EventCreate(event_type="warning", source="system", description=desc, priority=3)
                    await crud.create_event(db, event)