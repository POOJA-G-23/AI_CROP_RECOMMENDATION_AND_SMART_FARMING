"""
create_admin.py
===============
Run this ONCE to create the first admin account.

Usage:
  python create_admin.py
"""
import os, datetime, bcrypt
from pymongo import MongoClient

MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017/")
client = MongoClient(MONGO_URI)
db     = client["ai_crop_advisor"]
users  = db["users"]

print("=== Create Admin Account ===")
name  = input("Admin name   : ").strip() or "Admin"
email = input("Admin email  : ").strip().lower()
pw    = input("Admin password (min 6 chars): ").strip()

if len(pw) < 6:
    print("❌ Password too short"); exit(1)
if users.find_one({"email": email}):
    print("❌ Email already exists"); exit(1)

hashed = bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()
users.insert_one({"name":name,"email":email,"password":hashed,"role":"admin","createdAt":datetime.datetime.utcnow().isoformat()})
print(f"✅ Admin account created: {email}")
print("   You can now login at: http://localhost:5000/admin")
