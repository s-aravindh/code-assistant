"""Tests for memory management."""

import pytest
from pathlib import Path
from code_assistant.agent.memory import (
    parse_agent_md,
    create_agent_md_template,
    AGENT_MD_TEMPLATE,
)


class TestParseAgentMd:
    """Tests for parse_agent_md function."""
    
    def test_parse_existing_file(self, temp_project):
        """Test parsing an existing AGENT.md file."""
        agent_md = temp_project / "AGENT.md"
        agent_md.write_text("# Test Project\n\n## Overview\nThis is a test.\n")
        
        result = parse_agent_md(str(temp_project))
        
        assert result is not None
        assert "Test Project" in result
        assert "Overview" in result
    
    def test_parse_nonexistent_file(self, temp_project):
        """Test parsing when AGENT.md doesn't exist."""
        result = parse_agent_md(str(temp_project))
        
        assert result is None
    
    def test_parse_empty_file(self, temp_project):
        """Test parsing an empty AGENT.md file."""
        agent_md = temp_project / "AGENT.md"
        agent_md.write_text("")
        
        result = parse_agent_md(str(temp_project))
        
        # Empty content should be returned as empty string or None
        assert result == "" or result is None


class TestCreateAgentMdTemplate:
    """Tests for create_agent_md_template function."""
    
    def test_create_template_success(self, temp_dir):
        """Test creating AGENT.md template."""
        result = create_agent_md_template(str(temp_dir))
        
        assert "Successfully created" in result
        assert (temp_dir / "AGENT.md").exists()
    
    def test_create_template_uses_project_name(self, temp_dir):
        """Test that template uses project directory name."""
        create_agent_md_template(str(temp_dir))
        
        content = (temp_dir / "AGENT.md").read_text()
        assert temp_dir.name in content
    
    def test_create_template_already_exists(self, temp_project):
        """Test that creating template fails if file exists."""
        # Create existing AGENT.md
        (temp_project / "AGENT.md").write_text("Existing content")
        
        result = create_agent_md_template(str(temp_project))
        
        assert "already exists" in result
        # Content should not be overwritten
        assert (temp_project / "AGENT.md").read_text() == "Existing content"


class TestAgentMdTemplate:
    """Tests for the AGENT.md template content."""
    
    def test_template_has_sections(self):
        """Test that template has expected sections."""
        assert "# Project:" in AGENT_MD_TEMPLATE
        assert "## Overview" in AGENT_MD_TEMPLATE
        assert "## Tech Stack" in AGENT_MD_TEMPLATE
        assert "## Conventions" in AGENT_MD_TEMPLATE
        assert "## Architecture" in AGENT_MD_TEMPLATE
        assert "## Common Commands" in AGENT_MD_TEMPLATE
    
    def test_template_has_placeholder(self):
        """Test that template has project name placeholder."""
        assert "{project_name}" in AGENT_MD_TEMPLATE
