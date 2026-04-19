from database import get_db   # ← изменено
import crud                   # ← изменено
from config import settings   # ← изменено
import httpx

async def send_notification(event_type: str, description: str):
    async with httpx.AsyncClient() as client:
        try:
            await client.post(
                settings.NOTIFICATION_SERVICE_URL,
                json={"event_type": event_type, "description": description},
                timeout=5.0
            )
        except Exception as e:
            print(f"Failed to send notification: {e}")