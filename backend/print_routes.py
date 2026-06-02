from app.main import app
print("Loading routes...")
for route in app.routes:
    print(getattr(route, 'path', route.name))
