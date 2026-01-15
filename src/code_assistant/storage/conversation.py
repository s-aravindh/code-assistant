"""Conversation persistence utilities."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def save_conversation(
    session_id: str,
    messages: list[dict[str, Any]],
    filename: str,
    project_path: str | None = None,
    model_name: str | None = None,
    total_tokens: int = 0,
) -> str:
    """Save a conversation to a file.
    
    Args:
        session_id: The session ID
        messages: List of message dictionaries
        filename: Filename to save to (relative or absolute)
        project_path: Optional project path for context
        model_name: Optional model name for metadata
        total_tokens: Total tokens used in conversation
        
    Returns:
        Success or error message
    """
    try:
        path = Path(filename)
        
        # If relative path, save to current directory
        if not path.is_absolute():
            if project_path:
                path = Path(project_path) / path
            else:
                path = Path.cwd() / path
        
        # Ensure parent directory exists
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # Determine format from extension
        if path.suffix == ".json":
            return _save_as_json(path, session_id, messages, model_name, total_tokens)
        else:
            return _save_as_markdown(path, session_id, messages, model_name, total_tokens, project_path)
            
    except Exception as e:
        return f"Error saving conversation: {e}"


def _save_as_json(
    path: Path,
    session_id: str,
    messages: list[dict[str, Any]],
    model_name: str | None,
    total_tokens: int,
) -> str:
    """Save conversation as JSON."""
    data = {
        "session_id": session_id,
        "model": model_name,
        "total_tokens": total_tokens,
        "saved_at": datetime.now().isoformat(),
        "messages": messages,
    }
    
    path.write_text(json.dumps(data, indent=2), encoding='utf-8')
    return f"Conversation saved to {path}"


def _save_as_markdown(
    path: Path,
    session_id: str,
    messages: list[dict[str, Any]],
    model_name: str | None,
    total_tokens: int,
    project_path: str | None,
) -> str:
    """Save conversation as Markdown."""
    lines = [
        "# Conversation Log",
        "",
        f"- **Session**: {session_id[:8]}",
        f"- **Model**: {model_name or 'unknown'}",
        f"- **Tokens**: {total_tokens:,}",
        f"- **Project**: {project_path or 'N/A'}",
        f"- **Saved**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "---",
        "",
    ]
    
    for msg in messages:
        role = msg.get("role", "unknown")
        content = msg.get("content", "")
        
        if role == "user":
            lines.append(f"## User")
            lines.append("")
            lines.append(content)
            lines.append("")
        elif role == "assistant":
            lines.append(f"## Assistant")
            lines.append("")
            lines.append(content)
            lines.append("")
        elif role == "system":
            lines.append(f"## System")
            lines.append("")
            lines.append(f"*{content}*")
            lines.append("")
        
        lines.append("---")
        lines.append("")
    
    path.write_text("\n".join(lines), encoding='utf-8')
    return f"Conversation saved to {path}"


def load_conversation(filename: str) -> tuple[str | None, list[dict[str, Any]], str]:
    """Load a conversation from a file.
    
    Args:
        filename: Filename to load from
        
    Returns:
        Tuple of (session_id, messages, message)
    """
    try:
        path = Path(filename)
        
        if not path.exists():
            return None, [], f"File not found: {filename}"
        
        if path.suffix == ".json":
            return _load_from_json(path)
        else:
            return None, [], "Only JSON format is supported for loading conversations"
            
    except Exception as e:
        return None, [], f"Error loading conversation: {e}"


def _load_from_json(path: Path) -> tuple[str | None, list[dict[str, Any]], str]:
    """Load conversation from JSON."""
    data = json.loads(path.read_text(encoding='utf-8'))
    
    session_id = data.get("session_id")
    messages = data.get("messages", [])
    model = data.get("model", "unknown")
    tokens = data.get("total_tokens", 0)
    
    return session_id, messages, f"Loaded conversation: {len(messages)} messages, {tokens:,} tokens (model: {model})"
