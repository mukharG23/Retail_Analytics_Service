import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'database.db')

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS traffic_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            aisle TEXT NOT NULL,
            people_count INTEGER NOT NULL,
            timestamp TEXT NOT NULL
        )
    ''')

    conn.commit()
    conn.close()
    print("Database initialized successfully")

def log_traffic(filename, aisle, people_count):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    cursor.execute('''
        INSERT INTO traffic_logs (filename, aisle, people_count, timestamp)
        VALUES (?, ?, ?, ?)
    ''', (filename, aisle, people_count, timestamp))

    conn.commit()
    conn.close()
    print(f"Traffic logged: {aisle} - {people_count} people at {timestamp}")

def get_traffic_logs():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM traffic_logs ORDER BY timestamp DESC')
    rows = cursor.fetchall()
    conn.close()

    logs = []
    for row in rows:
        logs.append({
            'id': row[0],
            'filename': row[1],
            'aisle': row[2],
            'people_count': row[3],
            'timestamp': row[4]
        })

    return logs