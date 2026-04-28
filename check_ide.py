import os
import json
import sqlite3

appdata = os.getenv('APPDATA')
paths = [
    os.path.join(appdata, 'Code', 'User', 'globalStorage', 'state.vscdb'),
    os.path.join(appdata, 'Cursor', 'User', 'globalStorage', 'state.vscdb')
]
for p in paths:
    print(f"{p}: {os.path.exists(p)}")
    if os.path.exists(p):
        try:
            conn = sqlite3.connect(p)
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM ItemTable WHERE key='history.recentlyOpenedPathsList'")
            row = cursor.fetchone()
            if row:
                print("Found history.recentlyOpenedPathsList")
                data = json.loads(row[0])
                print(json.dumps(data, indent=2)[:500])
            conn.close()
        except Exception as e:
            print(f"Error reading {p}: {e}")
