import json
import zipfile
import os
from datetime import datetime
from typing import List, Optional
from .base import BaseCollector
from ..schema import Conversation, Message

class ClaudeCollector(BaseCollector):
    @property
    def name(self) -> str:
        return "claude"

    def collect(self, input_path: Optional[str] = None) -> List[Conversation]:
        if not input_path:
            raise ValueError("Claude collector requires path to export ZIP or JSON")

        if input_path.endswith(".zip"):
            with zipfile.ZipFile(input_path, "r") as z:
                # Find conversations.json
                json_filename = next((name for name in z.namelist() if "conversations" in name and name.endswith(".json")), None)
                if not json_filename:
                    raise ValueError("No conversations.json found in ZIP")
                
                with z.open(json_filename) as f:
                    data = json.load(f)
        else:
            with open(input_path, "r", encoding="utf-8") as f:
                data = json.load(f)

        return [self.parse_conversation(conv) for conv in data]

    def parse_conversation(self, conv: dict) -> Conversation:
        messages = []
        for msg in conv.get("chat_messages", []):
            role = "user" if msg["sender"] == "human" else "assistant"
            messages.append(Message(
                role=role,
                content=msg["text"],
                timestamp=msg["created_at"]
            ))

        return Conversation(
            id=self.generate_id("claude", conv["uuid"]),
            title=conv.get("name") or "Untitled",
            source="claude",
            createdAt=conv["created_at"],
            updatedAt=conv["updated_at"],
            messages=messages
        )
