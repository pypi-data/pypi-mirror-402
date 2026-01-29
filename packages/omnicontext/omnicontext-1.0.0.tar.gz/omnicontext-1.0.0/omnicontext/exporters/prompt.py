from typing import List, Dict, Any, Optional
from ..schema import Conversation

def export_prompt(
    conversations: List[Conversation],
    memories: List[Dict[str, str]] = [],
    max_tokens: Optional[int] = None,
    include_metadata: bool = False
) -> str:
    lines = []

    # Header
    lines.append('<context>')
    lines.append('The following is a summary of previous conversations and learned preferences from the user.')
    lines.append('Use this context to better understand the user and continue assisting them.')
    lines.append('</context>\n')

    # Memories first
    if memories:
        lines.append('<user_preferences>')
        for mem in memories:
            for key, value in mem.items():
                lines.append(f"- {key}: {value}")
        lines.append('</user_preferences>\n')

    # Conversations - most recent first
    lines.append('<conversation_history>')
    
    sorted_convs = sorted(conversations, key=lambda x: x.createdAt, reverse=True)

    for conv in sorted_convs:
        lines.append('')
        lines.append(f"### {conv.title}")
        if include_metadata:
            lines.append(f"Source: {conv.source} | Date: {conv.createdAt.split('T')[0]}")
        lines.append('')

        for msg in conv.messages:
            role = "User" if msg.role == "user" else "Assistant"
            content = truncate_content(msg.content, 500)
            lines.append(f"**{role}:** {content}\n")

    lines.append('</conversation_history>')

    result = "\n".join(lines)

    if max_tokens:
        max_chars = max_tokens * 4
        if len(result) > max_chars:
            result = result[:max_chars] + "\n\n[...truncated for token limit]"

    return result

def truncate_content(content: str, max_length: int) -> str:
    if len(content) <= max_length:
        return content
    return content[:max_length] + "..."
