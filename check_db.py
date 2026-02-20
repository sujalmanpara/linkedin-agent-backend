#!/usr/bin/env python3
import sqlite3

conn = sqlite3.connect('linkedin_agent.db')
cursor = conn.cursor()

# Get schema
cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='users'")
print("=== Users Table Schema ===")
print(cursor.fetchone()[0])

# Get all users
cursor.execute("SELECT user_id, linkedin_email, automation_enabled, daily_limits FROM users")
print("\n=== Users in Database ===")
for row in cursor.fetchall():
    print(f"User: {row[0]}, Email: {row[1]}, Automation: {row[2]}, Limits: {row[3]}")

conn.close()
