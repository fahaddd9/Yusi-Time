import asyncio
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

login_res = client.post("/api/v1/auth/login", json={"email": "thefadi384@gmail.com", "password": "Fadi@1234"})
token = login_res.json().get("access_token")

url = "/api/v1/time-entries?workspace_id=229bc373-21c5-436c-aef2-6aec8cf7e50d"
payload = {
  "project_id": "dae51421-7ab6-43f5-b636-d5c1b9714d95",
  "task_id": "ef003755-befa-4efc-a403-7d399fb2c2f3",
  "description": "Testing entry creation",
  "start_time": "2026-06-15T04:00:00.000Z",
  "end_time": "2026-06-15T05:00:00.000Z"
}

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

try:
    res = client.post(url, json=payload, headers=headers)
    print("Post status:", res.status_code)
    print("Post response:", res.text)
except Exception as e:
    import traceback
    traceback.print_exc()
