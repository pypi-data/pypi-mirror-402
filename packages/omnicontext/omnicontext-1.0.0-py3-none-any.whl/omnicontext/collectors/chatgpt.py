import json
from datetime import datetime
from typing import List, Optional
from .base import BaseCollector
from ..schema import Conversation, Message

class ChatGPTCollector(BaseCollector):
    @property
    def name(self) -> str:
        return "chatgpt"

    def collect(self, input_path: Optional[str] = None) -> List[Conversation]:
        if not input_path:
            raise ValueError("ChatGPT collector requires path to conversations.json")

        with open(input_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        return [self.parse_conversation(conv) for conv in data]

    def parse_conversation(self, conv: dict) -> Conversation:
        messages = []
        
        # Mapping items to list
        msg_entries = []
        for key, value in conv.get("mapping", {}).items():
            msg = value.get("message")
            if msg and msg.get("content") and msg["content"].get("parts"):
                msg_entries.append(msg)
        
        # Filter system and sort by time
        msg_entries = [m for m in msg_entries if m.get("author", {}).get("role") != "system"]
        msg_entries.sort(key=lambda x: x.get("create_time", 0))

        for msg in msg_entries:
            role = "user" if msg["author"]["role"] == "user" else "assistant"
            content = "\n".join(msg["content"]["parts"])
            
            if content.strip():
                timestamp = None
                if msg.get("create_time"):
                    timestamp = datetime.fromtimestamp(msg["create_time"]).isoformat()
                
                messages.append(Message(
                    role=role,
                    content=content,
                    timestamp=timestamp
                ))

        create_time = conv.get("create_time", 0)
        update_time = conv.get("update_time", 0)

        return Conversation(
            id=self.generate_id("chatgpt", conv["id"]),
            title=conv.get("title") or "Untitled",
            source="chatgpt",
            messages=messages,
            createdAt=datetime.fromtimestamp(create_time).isoformat() if create_time else datetime.now().isoformat(),
            updatedAt=datetime.fromtimestamp(update_time).isoformat() if update_time else datetime.now().isoformat()
        )
