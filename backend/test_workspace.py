
import asyncio, httpx
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.core.security import create_access_token
from app.core.config import get_settings

async def main():
    settings = get_settings()
    async with AsyncSessionLocal() as db:
        user = await db.scalar(select(User).where(User.email == 'test2@gmail.com').limit(1))
        token = create_access_token(str(user.id), settings=settings)
        
    async with httpx.AsyncClient() as client:
        res = await client.get(
            'http://localhost:8001/api/v1/workspaces/229bc373-21c5-436c-aef2-6aec8cf7e50d',
            headers={'Authorization': f'Bearer {token}'}
        )
        print(res.status_code, res.text)

asyncio.run(main())

