import asyncio
import sys
from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.models.attendance_notification import AttendanceNotification
from sqlalchemy import select
from datetime import datetime, UTC
from app.services import attendance_service

async def main():
    try:
        async with AsyncSessionLocal() as db:
            users = await db.execute(select(User).where(User.email == 'thefadi384@gmail.com'))
            user = users.scalar_one_or_none()
            if not user:
                print("No user Fadi")
                return
                
            print("User:", user.id)
            
            att_notifs = await db.execute(
                select(AttendanceNotification)
                .where(AttendanceNotification.recipient_user_id == user.id)
            )
            notifs = att_notifs.scalars().all()
            for n in notifs:
                print(f"Notif: {n.id}, type: {n.notification_type}, read_at: {n.read_at}, ws: {n.workspace_id}")
                
            # Try marking all read
            if notifs:
                await attendance_service.mark_all_read(db, notifs[0].workspace_id, user.id)
                await db.commit()
                print("Marked all read!")
                
                att_notifs2 = await db.execute(
                    select(AttendanceNotification)
                    .where(AttendanceNotification.recipient_user_id == user.id)
                )
                notifs2 = att_notifs2.scalars().all()
                for n in notifs2:
                    print(f"After: {n.id}, type: {n.notification_type}, read_at: {n.read_at}")
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
