"""
AIEMCS - One-time password fix script.
Run this once to set all incharge passwords to: incharge@123
Also creates a guaranteed admin account.

Usage: python fix_passwords.py
"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bcrypt
import pymysql
from dotenv import load_dotenv

load_dotenv()

DB_USER     = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "").replace("%40", "@")
DB_HOST     = os.getenv("DB_HOST", "localhost")
DB_PORT     = int(os.getenv("DB_PORT", "3306"))
DB_NAME     = os.getenv("DB_NAME", "aiemcs")

PLAIN_PASSWORD = "incharge@123"

print(f"Connecting to MySQL as {DB_USER}@{DB_HOST}:{DB_PORT}/{DB_NAME} ...")

try:
    conn = pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        charset="utf8mb4"
    )
    print("✅ Connected to MySQL!")
except Exception as e:
    print(f"❌ DB connection failed: {e}")
    sys.exit(1)

cursor = conn.cursor()

# ── Generate real bcrypt hash ──────────────────────────────────────────────────
print(f"\nGenerating bcrypt hash for '{PLAIN_PASSWORD}' ...")
real_hash = bcrypt.hashpw(PLAIN_PASSWORD.encode(), bcrypt.gensalt(rounds=12)).decode()
print(f"Hash: {real_hash[:30]}...")

# ── Update ALL incharge passwords ─────────────────────────────────────────────
print("\nUpdating all incharge passwords...")
cursor.execute("UPDATE incharge_data SET password_hash = %s", (real_hash,))
updated = cursor.rowcount
conn.commit()
print(f"✅ Updated {updated} incharge records.")

# ── Create guaranteed admin account ───────────────────────────────────────────
print("\nCreating guaranteed admin account...")

# Check if already exists
cursor.execute("SELECT incharge_id FROM incharge_data WHERE email = 'admin@aiemcs.com'")
existing = cursor.fetchone()

if existing:
    cursor.execute(
        "UPDATE incharge_data SET password_hash = %s WHERE email = 'admin@aiemcs.com'",
        (real_hash,)
    )
    print("✅ Admin account password reset.")
else:
    cursor.execute("""
        INSERT INTO incharge_data (incharge_id, name, email, phone, room_duty, password_hash, role)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (999999, 'Admin User', 'admin@aiemcs.com', '9000000000', 'E_001', real_hash, 'incharge'))
    print("✅ Admin account created.")

conn.commit()

# ── Show sample login credentials ─────────────────────────────────────────────
print("\nFetching sample login emails...")
cursor.execute("SELECT email FROM incharge_data LIMIT 5")
rows = cursor.fetchall()

print("\n" + "="*55)
print("  ✅ ALL DONE! You can now log in with:")
print("="*55)
print(f"  Password for ALL accounts: {PLAIN_PASSWORD}")
print("\n  Sample emails to use:")
for row in rows:
    print(f"    📧 {row[0]}")
print("\n  Or use the guaranteed admin account:")
print("    📧 admin@aiemcs.com")
print(f"    🔑 {PLAIN_PASSWORD}")
print("="*55)

cursor.close()
conn.close()