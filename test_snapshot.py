import os
import json
from datetime import datetime, timezone
os.makedirs("logs", exist_ok=True)
timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
snapshot_path = f"logs/snap_{timestamp}.json"

test_data = {
    "timestamp": timestamp,
    "pr_url": "https://github.com/test/test/pull/1",
    "test": "snapshot_generation",
    "status": "success"
}

try:
    with open(snapshot_path, 'w') as f:
        json.dump(test_data, f, indent=2)
    print(f"✅ Test snapshot created: {snapshot_path}")
except Exception as e:
    print(f"❌ Error: {e}")
