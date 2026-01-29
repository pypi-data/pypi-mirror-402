import json
import os
import zipfile
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Any
from .base import BaseCollector
from ..schema import Conversation, Message

class GrokCollector(BaseCollector):
    @property
    def name(self) -> str:
        return "grok"

    def collect(self, input_path: Optional[str] = None) -> List[Conversation]:
        if not input_path:
            raise ValueError("Grok collector requires path to X/Twitter data export")

        conversations = []
        path = Path(input_path)

        if path.suffix == ".zip":
            with zipfile.ZipFile(input_path, "r") as z:
                for entry in z.namelist():
                    lower_entry = entry.lower()
                    if ("grok" in lower_entry or "ai" in lower_entry or "chat" in lower_entry) and entry.endswith(".json"):
                        try:
                            with z.open(entry) as f:
                                data = json.load(f)
                            conversations.extend(self.parse_data(data, entry))
                        except:
                            continue
        else:
            with open(input_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            conversations.extend(self.parse_data(data, input_path))

        return conversations

    def parse_data(self, data: Any, source: str) -> List[Conversation]:
        conversations = []
        if isinstance(data, list):
            for i, item in enumerate(data):
                conv = self.parse_single_conversation(item, f"{source}_{i}")
                if conv.messages:
                    conversations.append(conv)
        elif isinstance(data, dict):
            conv = self.parse_single_conversation(data, source)
            if conv.messages:
                conversations.append(conv)
        return conversations

    def parse_single_conversation(self, data: Any, source: str) -> Conversation:
        messages = []
        if isinstance(data, dict):
            msg_array = data.get("messages") or data.get("conversation") or data.get("chat")
            if isinstance(msg_array, list):
                for msg in msg_array:
                    if msg.get("text") or msg.get("content"):
                        role_raw = msg.get("role") or msg.get("sender") or msg.get("author")
                        messages.append(Message(
                            role="user" if role_raw in ["user", "human"] else "assistant",
                            content=msg.get("text") or msg.get("content"),
                            timestamp=msg.get("timestamp") or msg.get("created_at")
                        ))

        return Conversation(
            id=self.generate_id("grok", Path(source).name),
            title="Grok Chat",
            source="grok",
            createdAt=datetime.now().isoformat(),
            updatedAt=datetime.now().isoformat(),
            messages=messages
        )
