import json
import os
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Any
from .base import BaseCollector
from ..schema import Conversation, Message

class AntigravityCollector(BaseCollector):
    @property
    def name(self) -> str:
        return "antigravity"

    def get_antigravity_dir(self) -> Path:
        return Path.home() / ".gemini" / "antigravity"

    def collect(self, input_path: Optional[str] = None) -> List[Conversation]:
        ag_dir = self.get_antigravity_dir()
        if not ag_dir.exists():
            raise ValueError(f"Antigravity directory not found: {ag_dir}")

        conversations = []
        brain_dir = ag_dir / "brain"
        if brain_dir.exists():
            for session_dir in brain_dir.iterdir():
                if session_dir.is_dir():
                    conv = self.parse_session(session_dir, session_dir.name)
                    if conv.messages:
                        conversations.append(conv)
        
        return conversations

    def parse_session(self, session_path: Path, session_id: str) -> Conversation:
        messages = []
        
        for file in session_path.iterdir():
            if not file.is_file():
                continue
            
            if file.suffix == ".json":
                try:
                    with open(file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    messages.extend(self.parse_json_file(data))
                except:
                    continue
            elif file.suffix == ".md":
                if file.name in ["task.md", "implementation_plan.md"]:
                    try:
                        with open(file, "r", encoding="utf-8") as f:
                            content = f.read()
                        messages.append(Message(
                            role="assistant",
                            content=f"[{file.name}]\n{content}"
                        ))
                    except:
                        continue

        return Conversation(
            id=self.generate_id("antigravity", session_id),
            title="Antigravity Session",
            source="antigravity",
            createdAt=datetime.now().isoformat(),
            updatedAt=datetime.now().isoformat(),
            messages=messages
        )

    def parse_json_file(self, data: Any) -> List[Message]:
        messages = []
        items = []
        if isinstance(data, list):
            items = data
        elif isinstance(data, dict):
            items = data.get("messages", [])

        for item in items:
            if item.get("role") and item.get("content"):
                content = item["content"]
                if not isinstance(content, str):
                    content = json.dumps(content)
                messages.append(Message(
                    role="user" if item["role"] == "user" else "assistant",
                    content=content,
                    timestamp=item.get("timestamp")
                ))
        return messages
