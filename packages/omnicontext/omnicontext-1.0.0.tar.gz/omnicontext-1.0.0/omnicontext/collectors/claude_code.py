import json
import os
from pathlib import Path
from datetime import datetime
from typing import List, Optional
from .base import BaseCollector
from ..schema import Conversation, Message

class ClaudeCodeCollector(BaseCollector):
    @property
    def name(self) -> str:
        return "claude-code"

    def get_claude_dir(self) -> Path:
        return Path.home() / ".claude"

    def collect(self, input_path: Optional[str] = None) -> List[Conversation]:
        claude_dir = self.get_claude_dir()
        if not claude_dir.exists():
            raise ValueError(f"Claude Code directory not found: {claude_dir}")

        conversations = []
        
        # Check projects
        projects_dir = claude_dir / "projects"
        if projects_dir.exists():
            for project_dir in projects_dir.iterdir():
                if project_dir.is_dir():
                    for file in project_dir.glob("*.json"):
                        try:
                            with open(file, "r", encoding="utf-8") as f:
                                data = json.load(f)
                            conv = self.parse_conversation_file(data, project_dir.name, file.name)
                            if conv.messages:
                                conversations.append(conv)
                        except:
                            continue

        # Check root files
        for file in claude_dir.glob("*.json"):
            if file.name != "settings.json":
                try:
                    with open(file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    conv = self.parse_conversation_file(data, "root", file.name)
                    if conv.messages:
                        conversations.append(conv)
                except:
                    continue

        return conversations

    def parse_conversation_file(self, data: any, project: str, filename: str) -> Conversation:
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

        return Conversation(
            id=self.generate_id("claude-code", f"{project}_{filename}"),
            title=project if project != "root" else filename.replace(".json", ""),
            source="claude-code",
            createdAt=datetime.now().isoformat(),
            updatedAt=datetime.now().isoformat(),
            messages=messages
        )
