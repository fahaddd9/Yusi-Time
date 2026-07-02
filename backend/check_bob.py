import asyncio, httpx
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.core.security import create_access_token
from app.core.config import get_settings

async def main():
    settings = get_settings()
    async with AsyncSessionLocal() as db:
        # Bob is the member - check bob@email.com
        user = await db.scalar(select(User).where(User.email == 'bob@email.com').limit(1))
        if not user:
            print("ERROR: bob@email.com not found")
            return
        token = create_access_token(str(user.id), settings=settings)
        
    async with httpx.AsyncClient() as client:
        # Test 1: check attendance notifications
        print("=== Test 1: /notifications/attendance ===")
        res = await client.get(
            'http://localhost:8001/api/v1/notifications/attendance?workspace_id=229bc373-21c5-436c-aef2-6aec8cf7e50d&scope=self&per_page=10',
            headers={'Authorization': f'Bearer {token}'}
        )
        print(res.status_code, res.text[:500])
        
        print("\n=== Test 2: /time-entries/daily-progress ===")
        res2 = await client.get(
            'http://localhost:8001/api/v1/time-entries/daily-progress?workspace_id=229bc373-21c5-436c-aef2-6aec8cf7e50d',
            headers={'Authorization': f'Bearer {token}'}
        )
        print(res2.status_code, res2.text)
        
        print("\n=== Test 3: /workspaces/229bc373... (workspace detail) ===")
        res3 = await client.get(
            'http://localhost:8001/api/v1/workspaces/229bc373-21c5-436c-aef2-6aec8cf7e50d',
            headers={'Authorization': f'Bearer {token}'}
        )
        print(res3.status_code, res3.text[:500])

asyncio.run(main())
