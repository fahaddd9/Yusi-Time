import httpx

login_res = httpx.post("http://localhost:8001/api/v1/auth/login", json={"email": "thefadi384@gmail.com", "password": "Fadi@1234"})
token = login_res.json().get("access_token")

url = "http://localhost:8001/api/v1/time-entries?workspace_id=229bc373-21c5-436c-aef2-6aec8cf7e50d&date_from=2026-06-14&date_to=2026-06-20"
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

res = httpx.get(url, headers=headers)
print("GET status:", res.status_code)
print("GET response:", res.text)
