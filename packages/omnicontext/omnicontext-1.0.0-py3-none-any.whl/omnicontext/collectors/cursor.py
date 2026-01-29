import sqlite3
import json
import os
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Any
from .base import BaseCollector
from ..schema import Conversation, Message

class CursorCollector(BaseCollector):
    @property
    def name(self) -> str:
        return "cursor"

    def get_cursor_db_path(self) -> Path:
        if os.name == 'nt':
            appdata = os.getenv('APPDATA', '')
            return Path(appdata) / 'Cursor' / 'User' / 'globalStorage' / 'state.vscdb'
        elif os.name == 'posix': # Mac/Linux
            home = Path.home()
            # Try mac path
            mac_path = home / 'Library' / 'Application Support' / 'Cursor' / 'User' / 'globalStorage' / 'state.vscdb'
            if mac_path.exists():
                return mac_path
            # Fallback to linux
            return home / '.config' / 'Cursor' / 'User' / 'globalStorage' / 'state.vscdb'
        return Path('')

    def collect(self, input_path: Optional[str] = None) -> List[Conversation]:
        db_path = self.get_cursor_db_path()
        if not db_path.exists():
            raise ValueError(f"Cursor database not found: {db_path}")

        conversations = []
        try:
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Use LIKE for broad matching
            cursor.execute("""
                SELECT key, value FROM ItemTable 
                WHERE key LIKE '%chat%' OR key LIKE '%conversation%' OR key LIKE '%composer%'
            """)
            
            for row in cursor.fetchall():
                key = row["key"]
                value = row["value"]
                
                try:
                    data = json.loads(value)
                    conv = self.parse_data(data, key)
                    if conv and conv.messages:
                        conversations.append(conv)
                except:
                    continue
            
            conn.close()
        except Exception as e:
            raise ValueError(f"Error reading Cursor DB: {str(e)}")

        return conversations

    def parse_data(self, data: Any, key: str) -> Optional[Conversation]:
        messages = []
        
        items = []
        if isinstance(data, list):
            items = data
        elif isinstance(data, dict):
            items = data.get("messages", []) or data.get("conversation", [])

        for item in items:
            if self.is_message(item):
                messages.append(self.to_omni_message(item))

        if not messages:
            return None

        return Conversation(
            id=self.generate_id("cursor", key),
            title=self.extract_title(messages) or key,
            source="cursor",
            createdAt=datetime.now().isoformat(),
            updatedAt=datetime.now().isoformat(),
            messages=messages
        )

    def is_message(self, obj: Any) -> bool:
        if not isinstance(obj, dict):
            return False
        return (obj.get("role") or obj.get("type")) and (obj.get("content") or obj.get("text"))

    def to_omni_message(self, msg: dict) -> Message:
        role_raw = msg.get("role") or msg.get("type") or "user"
        role = "user" if role_raw in ["user", "human"] else "assistant"
        content = msg.get("content") or msg.get("text") or ""
        return Message(role=role, content=content)

    def extract_title(self, messages: List[Message]) -> str:
        for msg in messages:
            if msg.role == "user":
                return (msg.content[:50] + "...") if len(msg.content) > 50 else msg.content
        return "Cursor Chat"
