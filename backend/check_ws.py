import asyncio, httpx
from app.core.security import create_access_token
from app.core.config import get_settings

async def main():
    s = get_settings()
    t = create_access_token('ef09d5af-818c-4310-8d52-7aec4bc9946d', settings=s)
    async with httpx.AsyncClient() as c:
        r2 = await c.get('http://localhost:8001/api/v1/workspaces/229bc373-21c5-436c-aef2-6aec8cf7e50d', headers={'Authorization': 'Bearer '+t})
        print("/workspaces/229bc373 STATUS:", r2.status_code)
        print("/workspaces/229bc373 BODY:", r2.text)

asyncio.run(main())
