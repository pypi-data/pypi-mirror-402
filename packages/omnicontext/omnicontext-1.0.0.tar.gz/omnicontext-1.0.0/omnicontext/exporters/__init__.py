from typing import List, Dict, Any, Optional, Literal
from .markdown import export_markdown
from .prompt import export_prompt
from .json import export_json
from ..schema import Conversation

ExportFormat = Literal["markdown", "prompt", "json"]

def export_as(
    format: ExportFormat,
    conversations: List[Conversation],
    memories: List[Dict[str, str]] = [],
    options: Dict[str, Any] = {}
) -> str:
    if format == "markdown":
        return export_markdown(conversations)
    elif format == "prompt":
        return export_prompt(
            conversations,
            memories,
            max_tokens=options.get("max_tokens"),
            include_metadata=options.get("include_metadata", False)
        )
    elif format == "json":
        return export_json(conversations, memories)
    else:
        raise ValueError(f"Unknown export format: {format}")
