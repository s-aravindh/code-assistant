"""Tests for slash command handling."""

import pytest
from code_assistant.utils.slash_commands import SlashCommandHandler


class TestSlashCommandHandler:
    """Tests for SlashCommandHandler class."""
    
    def test_is_slash_command(self, slash_handler):
        """Test detecting slash commands."""
        assert slash_handler.is_slash_command("/help") is True
        assert slash_handler.is_slash_command("/clear") is True
        assert slash_handler.is_slash_command("  /model test") is True
        
        assert slash_handler.is_slash_command("hello") is False
        assert slash_handler.is_slash_command("not a /command") is False
    
    def test_parse_command(self, slash_handler):
        """Test parsing slash commands."""
        command, args = slash_handler.parse_command("/help")
        assert command == "/help"
        assert args == []
        
        command, args = slash_handler.parse_command("/model openai:gpt-4o")
        assert command == "/model"
        assert args == ["openai:gpt-4o"]
        
        command, args = slash_handler.parse_command("/plan add user authentication")
        assert command == "/plan"
        assert args == ["add", "user", "authentication"]


class TestHelpCommand:
    """Tests for /help command."""
    
    def test_help_returns_info(self, slash_handler):
        """Test /help returns help text."""
        result = slash_handler.execute("/help")
        
        assert result["type"] == "info"
        assert "Available Commands" in result["message"]
        assert "/help" in result["message"]


class TestClearCommand:
    """Tests for /clear command."""
    
    def test_clear_returns_action(self, slash_handler):
        """Test /clear returns clear action."""
        result = slash_handler.execute("/clear")
        
        assert result["type"] == "action"
        assert result["action"] == "clear"


class TestExitCommand:
    """Tests for /exit and /quit commands."""
    
    def test_exit_returns_action(self, slash_handler):
        """Test /exit returns exit action."""
        result = slash_handler.execute("/exit")
        
        assert result["type"] == "action"
        assert result["action"] == "exit"
    
    def test_quit_returns_action(self, slash_handler):
        """Test /quit also returns exit action."""
        result = slash_handler.execute("/quit")
        
        assert result["type"] == "action"
        assert result["action"] == "exit"


class TestModelCommand:
    """Tests for /model command."""
    
    def test_model_with_arg(self, slash_handler):
        """Test /model with model name."""
        result = slash_handler.execute("/model openai:gpt-4o")
        
        assert result["type"] == "action"
        assert result["action"] == "switch_model"
        assert result["model"] == "openai:gpt-4o"
    
    def test_model_without_arg(self, slash_handler):
        """Test /model without argument returns error."""
        result = slash_handler.execute("/model")
        
        assert result["type"] == "error"
        assert "Usage" in result["message"]


class TestPlanCommand:
    """Tests for /plan command."""
    
    def test_plan_with_requirement(self, slash_handler):
        """Test /plan with requirement."""
        result = slash_handler.execute("/plan add user authentication")
        
        assert result["type"] == "action"
        assert result["action"] == "run_plan_agent"
        assert result["requirement"] == "add user authentication"
    
    def test_plan_without_arg(self, slash_handler):
        """Test /plan without argument returns error."""
        result = slash_handler.execute("/plan")
        
        assert result["type"] == "error"
        assert "Usage" in result["message"]


class TestBugCommand:
    """Tests for /bug command."""
    
    def test_bug_with_description(self, slash_handler):
        """Test /bug with description."""
        result = slash_handler.execute("/bug the login button doesn't work")
        
        assert result["type"] == "action"
        assert result["action"] == "debug_bug"
        assert "login button" in result["description"]
    
    def test_bug_without_arg(self, slash_handler):
        """Test /bug without argument returns error."""
        result = slash_handler.execute("/bug")
        
        assert result["type"] == "error"


class TestUnknownCommand:
    """Tests for unknown commands."""
    
    def test_unknown_command_returns_error(self, slash_handler):
        """Test unknown command returns error."""
        result = slash_handler.execute("/unknowncommand")
        
        assert result["type"] == "error"
        assert "Unknown command" in result["message"]
