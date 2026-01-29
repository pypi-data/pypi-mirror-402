import json
from datetime import datetime
from typing import List, Dict, Any

def export_json(conversations: List[any], memories: List[Dict[str, str]] = []) -> str:
    data = {
        "version": "1.0",
        "exportedAt": datetime.now().isoformat(),
        "conversations": [c.model_dump() for c in conversations],
        "memories": memories
    }
    return json.dumps(data, indent=2)
