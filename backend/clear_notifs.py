
import asyncio, asyncpg

async def main():
    conn = await asyncpg.connect('postgresql://yusitime:yusitime_dev@localhost:5432/yusitime')
    deleted = await conn.execute('DELETE FROM attendance_notifications;')
    print('Cleared:', deleted)
    row = await conn.fetchrow('''
        SELECT id, default_timezone, work_start_time, attendance_enabled, attendance_mode, off_days
        FROM workspaces WHERE id = chr(50) || chr(50) || chr(57) || 'bc373-21c5-436c-aef2-6aec8cf7e50d'
    ''')
    if row:
        print('Workspace found')
    else:
        row = await conn.fetchrow('SELECT id, default_timezone, work_start_time, attendance_enabled, attendance_mode FROM workspaces LIMIT 1')
        print('First workspace:', dict(row))
    await conn.close()

asyncio.run(main())

