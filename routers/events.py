from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, or_
from database import get_db
from models import Event

router = APIRouter(prefix="/api/v1/events", tags=["events"])

@router.get("/")
async def get_events(
    limit: int = 100,
    all_events: bool = Query(False, description="Если true, вернуть все события без фильтрации"),
    db: AsyncSession = Depends(get_db)
):
    if all_events:
        stmt = select(Event).order_by(desc(Event.timestamp)).limit(limit)
    else:
        keywords = [
            "Аномалия",
            "Нагреватель",
            "Освещение",
            "режим освещения",
            "целевая температура",
            "кормление",
            "Устройство",
            "Мощность",
            "Режим устройства",
            "включено",
            "выключено"
        ]
        conditions = [Event.description.contains(kw) for kw in keywords]
        stmt = select(Event).where(or_(*conditions)).order_by(desc(Event.timestamp)).limit(limit)
    result = await db.execute(stmt)
    events = result.scalars().all()
    return events