import json
import os
import zipfile
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Any
from .base import BaseCollector
from ..schema import Conversation, Message

class GeminiCollector(BaseCollector):
    @property
    def name(self) -> str:
        return "gemini"

    def collect(self, input_path: Optional[str] = None) -> List[Conversation]:
        if not input_path:
            raise ValueError("Gemini collector requires path to Google Takeout ZIP or extracted folder")

        conversations = []
        path = Path(input_path)

        if path.suffix == ".zip":
            with zipfile.ZipFile(input_path, "r") as z:
                for entry in z.namelist():
                    if ("Gemini" in entry or "Bard" in entry) and entry.endswith(".json"):
                        try:
                            with z.open(entry) as f:
                                data = json.load(f)
                            conv = self.parse_conversation(data, entry)
                            if conv.messages:
                                conversations.append(conv)
                        except:
                            continue
        elif path.is_dir():
            for file in path.rglob("*.json"):
                if "Gemini" in str(file) or "Bard" in str(file):
                    try:
                        with open(file, "r", encoding="utf-8") as f:
                            data = json.load(f)
                        conv = self.parse_conversation(data, str(file))
                        if conv.messages:
                            conversations.append(conv)
                    except:
                        continue
        else:
            with open(input_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            conv = self.parse_conversation(data, input_path)
            if conv.messages:
                conversations.append(conv)

        return conversations

    def parse_conversation(self, data: Any, source: str) -> Conversation:
        messages = []
        
        if isinstance(data, list):
            for item in data:
                if item.get("text") and item.get("role"):
                    messages.append(Message(
                        role="user" if item["role"] == "user" else "assistant",
                        content=item["text"]
                    ))
        elif isinstance(data, dict):
            if isinstance(data.get("conversations"), list):
                for conv in data["conversations"]:
                    if isinstance(conv.get("messages"), list):
                        for msg in conv["messages"]:
                            if msg.get("text"):
                                messages.append(Message(
                                    role="user" if msg.get("author") == "user" else "assistant",
                                    content=msg["text"]
                                ))

        return Conversation(
            id=self.generate_id("gemini", Path(source).name),
            title=Path(source).stem or "Gemini Chat",
            source="gemini",
            createdAt=datetime.now().isoformat(),
            updatedAt=datetime.now().isoformat(),
            messages=messages
        )
