from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

print("--- Testing /invalid ---")
response = client.get("/invalid")
print("Status:", response.status_code)
print("JSON:", response.json())
print("X-Request-ID:", response.headers.get("x-request-id"))

print("\n--- Testing /health ---")
response2 = client.get("/health")
print("Status:", response2.status_code)
print("JSON:", response2.json())
print("X-Request-ID:", response2.headers.get("x-request-id"))
