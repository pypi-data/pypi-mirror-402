from .base import BaseCollector
from .chatgpt import ChatGPTCollector
from .claude import ClaudeCollector
from .claude_code import ClaudeCodeCollector
from .cursor import CursorCollector
from .gemini import GeminiCollector
from .grok import GrokCollector
from .antigravity import AntigravityCollector

def get_collector(source: str) -> BaseCollector:
    collectors = {
        "chatgpt": ChatGPTCollector(),
        "claude": ClaudeCollector(),
        "claude-code": ClaudeCodeCollector(),
        "cursor": CursorCollector(),
        "gemini": GeminiCollector(),
        "grok": GrokCollector(),
        "antigravity": AntigravityCollector(),
    }
    
    if source not in collectors:
        raise ValueError(f"Unknown source: {source}. Available: {', '.join(collectors.keys())}")
        
    return collectors[source]
