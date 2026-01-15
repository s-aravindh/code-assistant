"""Tests for conversation persistence."""

import pytest
import json
from pathlib import Path
from code_assistant.storage.conversation import save_conversation, load_conversation


class TestSaveConversation:
    """Tests for save_conversation function."""
    
    def test_save_as_markdown(self, temp_dir):
        """Test saving conversation as markdown."""
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
        ]
        
        result = save_conversation(
            session_id="test-session",
            messages=messages,
            filename=str(temp_dir / "conversation.md"),
        )
        
        assert "saved" in result.lower()
        assert (temp_dir / "conversation.md").exists()
        
        content = (temp_dir / "conversation.md").read_text()
        assert "User" in content
        assert "Hello" in content
        assert "Assistant" in content
        assert "Hi there!" in content
    
    def test_save_as_json(self, temp_dir):
        """Test saving conversation as JSON."""
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi!"},
        ]
        
        result = save_conversation(
            session_id="test-session",
            messages=messages,
            filename=str(temp_dir / "conversation.json"),
            model_name="test-model",
            total_tokens=100,
        )
        
        assert "saved" in result.lower()
        
        data = json.loads((temp_dir / "conversation.json").read_text())
        assert data["session_id"] == "test-session"
        assert data["model"] == "test-model"
        assert data["total_tokens"] == 100
        assert len(data["messages"]) == 2
    
    def test_save_creates_directory(self, temp_dir):
        """Test that save creates parent directories."""
        messages = [{"role": "user", "content": "Test"}]
        
        result = save_conversation(
            session_id="test",
            messages=messages,
            filename=str(temp_dir / "subdir" / "conversation.md"),
        )
        
        assert "saved" in result.lower()
        assert (temp_dir / "subdir" / "conversation.md").exists()


class TestLoadConversation:
    """Tests for load_conversation function."""
    
    def test_load_json_conversation(self, temp_dir):
        """Test loading a JSON conversation."""
        data = {
            "session_id": "loaded-session",
            "model": "test-model",
            "total_tokens": 500,
            "messages": [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi!"},
            ],
        }
        
        json_file = temp_dir / "conversation.json"
        json_file.write_text(json.dumps(data))
        
        session_id, messages, msg = load_conversation(str(json_file))
        
        assert session_id == "loaded-session"
        assert len(messages) == 2
        assert "Loaded" in msg
    
    def test_load_nonexistent_file(self, temp_dir):
        """Test loading a non-existent file."""
        session_id, messages, msg = load_conversation(
            str(temp_dir / "nonexistent.json")
        )
        
        assert session_id is None
        assert messages == []
        assert "not found" in msg.lower()
    
    def test_load_non_json_not_supported(self, temp_dir):
        """Test that loading non-JSON files is not supported."""
        md_file = temp_dir / "conversation.md"
        md_file.write_text("# Conversation\n\n## User\nHello")
        
        session_id, messages, msg = load_conversation(str(md_file))
        
        assert session_id is None
        assert "not supported" in msg.lower() or "Only JSON" in msg
