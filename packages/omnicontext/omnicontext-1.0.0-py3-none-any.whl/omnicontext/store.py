import sqlite3
import json
import os
from pathlib import Path
from typing import List, Optional, Dict, Any
from .schema import Conversation, Message

DB_PATH = Path.home() / ".omni.db"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    setup_db(conn)
    return conn

def setup_db(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id TEXT PRIMARY KEY,
            title TEXT,
            source TEXT,
            messages TEXT,
            createdAt TEXT,
            updatedAt TEXT,
            selected INTEGER DEFAULT 0,
            metadata TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS config (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)
    conn.commit()

def save_conversations(conversations: List[Conversation]):
    conn = get_db()
    for conv in conversations:
        conn.execute("""
            INSERT OR REPLACE INTO conversations 
            (id, title, source, messages, createdAt, updatedAt, selected, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            conv.id,
            conv.title,
            conv.source,
            json.dumps([m.model_dump() for m in conv.messages]),
            conv.createdAt,
            conv.updatedAt,
            1 if conv.selected else 0,
            json.dumps(conv.metadata)
        ))
    conn.commit()
    conn.close()

def get_conversations(source: Optional[str] = None, selected: bool = False) -> List[Conversation]:
    conn = get_db()
    query = "SELECT * FROM conversations WHERE 1=1"
    params = []
    
    if source:
        query += " AND source = ?"
        params.append(source)
    if selected:
        query += " AND selected = 1"
    
    query += " ORDER BY createdAt DESC"
    
    rows = conn.execute(query, params).fetchall()
    conn.close()
    
    results = []
    for row in rows:
        results.append(Conversation(
            id=row["id"],
            title=row["title"],
            source=row["source"],
            messages=[Message(**m) for m in json.loads(row["messages"])],
            createdAt=row["createdAt"],
            updatedAt=row["updatedAt"],
            selected=bool(row["selected"]),
            metadata=json.loads(row["metadata"])
        ))
    return results

def select_conversations(ids: List[str]):
    conn = get_db()
    for conv_id in ids:
        conn.execute("UPDATE conversations SET selected = 1 WHERE id LIKE ?", (f"%{conv_id}%",))
    conn.commit()
    conn.close()

def select_all():
    conn = get_db()
    conn.execute("UPDATE conversations SET selected = 1")
    conn.commit()
    conn.close()

def clear_selection():
    conn = get_db()
    conn.execute("UPDATE conversations SET selected = 0")
    conn.commit()
    conn.close()

def get_selected_conversations() -> List[Conversation]:
    return get_conversations(selected=True)

def get_config() -> Dict[str, Any]:
    conn = get_db()
    rows = conn.execute("SELECT * FROM config").fetchall()
    conn.close()
    return {row["key"]: row["value"] for row in rows}

def set_config(key: str, value: str):
    conn = get_db()
    conn.execute("INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)", (key, value))
    conn.commit()
    conn.close()

def get_stats() -> Dict[str, Any]:
    conn = get_db()
    total = conn.execute("SELECT COUNT(*) FROM conversations").fetchone()[0]
    selected = conn.execute("SELECT COUNT(*) FROM conversations WHERE selected = 1").fetchone()[0]
    
    sources_rows = conn.execute("SELECT source, COUNT(*) FROM conversations GROUP BY source").fetchall()
    sources = {row[0]: row[1] for row in sources_rows}
    
    conn.close()
    return {
        "total": total,
        "selected": selected,
        "sources": sources
    }
