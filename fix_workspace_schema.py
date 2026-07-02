import re

file_path = 'd:/yusi time/backend/app/schemas/workspace.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('from datetime import datetime', 'from datetime import datetime, time')
content = content.replace('work_start_time: Optional[datetime] = None', 'work_start_time: Optional[time] = None')

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print('Done!')
