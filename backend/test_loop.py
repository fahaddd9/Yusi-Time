import urllib.request
import urllib.error

for i in range(10):
    try:
        req = urllib.request.Request('http://127.0.0.1:8000/api/v1/users/me')
        with urllib.request.urlopen(req) as response:
            pass
    except urllib.error.HTTPError as e:
        print(f"Request {i}: HTTPError {e.code}")
    except Exception as e:
        print(f"Request {i}: Error {e}")
