import asyncio, httpx
from app.core.security import create_access_token
from app.core.config import get_settings

async def main():
    s = get_settings()
    t = create_access_token('ef09d5af-818c-4310-8d52-7aec4bc9946d', settings=s)
    async with httpx.AsyncClient() as c:
        r = await c.get('http://localhost:8001/api/v1/notifications/attendance?workspace_id=229bc373-21c5-436c-aef2-6aec8cf7e50d', headers={'Authorization': 'Bearer '+t})
        with open('test2_notifs.txt', 'w') as f:
            f.write(str(r.status_code) + '\n' + r.text)

if __name__ == '__main__':
    asyncio.run(main())
