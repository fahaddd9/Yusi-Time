import asyncio, httpx
from app.core.security import create_access_token
from app.core.config import get_settings

async def main():
    s = get_settings()
    t = create_access_token('dfd79611-75b0-4633-b96a-2e8cb809ece7', settings=s)
    async with httpx.AsyncClient() as c:
        r = await c.get('http://localhost:8001/api/v1/notifications', params={'workspace_id': '229bc373-21c5-436c-aef2-6aec8cf7e50d'}, headers={'Authorization': 'Bearer '+t})
        print("/notifications STATUS:", r.status_code)
        print("/notifications BODY:", r.text)
        
        r2 = await c.get('http://localhost:8001/api/v1/notifications/attendance', params={'workspace_id': '229bc373-21c5-436c-aef2-6aec8cf7e50d'}, headers={'Authorization': 'Bearer '+t})
        print("/notifications/attendance STATUS:", r2.status_code)
        print("/notifications/attendance BODY:", r2.text)

asyncio.run(main())
