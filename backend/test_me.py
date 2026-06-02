import urllib.request
import urllib.error
try:
    req = urllib.request.Request('http://127.0.0.1:8000/api/v1/users/me')
    with urllib.request.urlopen(req) as response:
        print("200 OK")
        print(response.read().decode())
except urllib.error.HTTPError as e:
    print(f"HTTPError: {e.code}")
    print(e.read().decode())
except Exception as e:
    print(f"Error: {e}")
