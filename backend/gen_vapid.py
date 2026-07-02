from py_vapid import Vapid
import os

vapid = Vapid()
vapid.generate_keys()
private_key = vapid.private_key_b64()
public_key = vapid.public_key_b64()

print("VAPID_PRIVATE_KEY=" + private_key.decode('utf-8'))
print("VAPID_PUBLIC_KEY=" + public_key.decode('utf-8'))
print("NEXT_PUBLIC_VAPID_PUBLIC_KEY=" + public_key.decode('utf-8'))
