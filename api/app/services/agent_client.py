from typing import Optional
import httpx
from ..settings import settings

async def generate_report(payload: dict) -> Optional[str]:
    if not settings.agent_enabled:
        return None

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.post(f"{settings.agent_base_url}/report", json=payload)
            r.raise_for_status()
            data = r.json()
            return data.get("report_summary")
    except Exception:
        # In MVP: do not fail the decision endpoint if agent fails
        return None
