from datetime import datetime
from typing import List
from ..schema import Conversation

def export_markdown(conversations: List[Conversation]) -> str:
    lines = []
    lines.append('# Conversation Export')
    lines.append('')
    lines.append(f"*Exported {len(conversations)} conversations on {datetime.now().isoformat()}*")
    lines.append('')
    lines.append('---')
    lines.append('')

    for conv in conversations:
        lines.append(f"## {conv.title}")
        lines.append('')
        lines.append(f"*Source: {conv.source} | Created: {conv.createdAt}*")
        lines.append('')

        for msg in conv.messages:
            prefix = "**You:**" if msg.role == "user" else "**Assistant:**"
            lines.append(prefix)
            lines.append('')
            lines.append(msg.content)
            lines.append('')

        lines.append('---')
        lines.append('')

    return "\n".join(lines)
