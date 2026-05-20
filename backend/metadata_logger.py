import os
import json
from datetime import datetime

LOG_FILE = os.path.join(os.path.dirname(__file__), '..', 'logs', 'metadata_log.json')

def log_metadata(filename, filepath):
    size = os.path.getsize(filepath)
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    entry = {
        'filename': filename,
        'size_bytes': size,
        'uploaded_at': timestamp
    }

    with open(LOG_FILE, 'r') as f:
        logs = json.load(f)

    logs.append(entry)

    with open(LOG_FILE, 'w') as f:
        json.dump(logs, f, indent=2)