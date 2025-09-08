"""
Unit tests for PromptManager service.
"""
import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, mock_open
from app.services.prompt_manager import PromptManager, PromptTemplate, PromptManagerError


@pytest.mark.unit
class TestPromptTemplate:
    """Test PromptTemplate data model."""
    
    def test_prompt_template_creation(self):
        """Test creating PromptTemplate with valid data."""
        template = PromptTemplate(
            category="test",
            name="test_prompt",
            version="1.0.0",
            description="Test prompt",
            last_updated="2024-09-08",
            tags=["test", "unit"],
            variables=["name", "context"],
            template="Hello {name}, context: {context}"
        )
        
        assert template.category == "test"
        assert template.name == "test_prompt"
        assert template.version == "1.0.0"
        assert len(template.variables) == 2
        assert "name" in template.variables
        assert "context" in template.variables
    
    def test_prompt_template_format_success(self):
        """Test successful template formatting."""
        template = PromptTemplate(
            category="test",
            name="test_prompt",
            version="1.0.0",
            description="Test prompt",
            last_updated="2024-09-08",
            variables=["name", "greeting"],
            template="Hello {name}! {greeting}"
        )
        
        result = template.format(name="Alice", greeting="How are you?")
        assert result == "Hello Alice! How are you?"
    
    def test_prompt_template_format_missing_variables(self):
        """Test template formatting with missing variables."""
        template = PromptTemplate(
            category="test",
            name="test_prompt",
            version="1.0.0",
            description="Test prompt",
            last_updated="2024-09-08",
            variables=["name", "greeting"],
            template="Hello {name}! {greeting}"
        )
        
        with pytest.raises(ValueError, match="Missing required variables"):
            template.format(name="Alice")  # Missing 'greeting'


@pytest.mark.unit
class TestPromptManager:
    """Test PromptManager functionality."""
    
    @pytest.fixture
    def temp_prompts_dir(self):
        """Create a temporary prompts directory for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            prompts_dir = Path(tmpdir) / "prompts"
            prompts_dir.mkdir()
            
            # Create config.yaml
            config_content = """
version: 1.0.0
description: Test prompt configuration

categories:
  social:
    description: "Social interactions"
    file: "social.yaml"
  professional:
    description: "Professional communications"
    file: "professional.yaml"

settings:
  hot_reload_enabled: true
  cache_duration: 300
  default_language: "en"
"""
            (prompts_dir / "config.yaml").write_text(config_content)
            
            # Create social.yaml
            social_content = """
category: social
name: test_social
version: 1.0.0
description: Test social prompt
last_updated: "2024-09-08"
tags: [social, test]
variables:
  - name
  - message
template: |
  Social interaction: {name}
  Message: {message}
"""
            (prompts_dir / "social.yaml").write_text(social_content)
            
            # Create professional.yaml
            professional_content = """
category: professional
name: test_professional
version: 1.0.0
description: Test professional prompt
last_updated: "2024-09-08"
tags: [professional, test]
variables:
  - context
  - objective
template: |
  Professional context: {context}
  Objective: {objective}
"""
            (prompts_dir / "professional.yaml").write_text(professional_content)
            
            yield prompts_dir
    
    def test_prompt_manager_initialization(self, temp_prompts_dir):
        """Test PromptManager initialization with valid directory."""
        manager = PromptManager(prompts_dir=str(temp_prompts_dir))
        
        assert manager.prompts_dir == temp_prompts_dir
        assert len(manager._prompt_cache) == 2  # social and professional
        assert "social" in manager._prompt_cache
        assert "professional" in manager._prompt_cache
    
    def test_get_prompt_success(self, temp_prompts_dir):
        """Test successful prompt retrieval."""
        manager = PromptManager(prompts_dir=str(temp_prompts_dir))
        
        social_prompt = manager.get_prompt("social")
        
        assert isinstance(social_prompt, PromptTemplate)
        assert social_prompt.category == "social"
        assert social_prompt.name == "test_social"
        assert "name" in social_prompt.variables
        assert "message" in social_prompt.variables
    
    def test_get_prompt_unknown_category(self, temp_prompts_dir):
        """Test error when requesting unknown category."""
        manager = PromptManager(prompts_dir=str(temp_prompts_dir))
        
        with pytest.raises(PromptManagerError, match="Unknown category"):
            manager.get_prompt("unknown_category")
    
    def test_list_categories(self, temp_prompts_dir):
        """Test listing all available categories."""
        manager = PromptManager(prompts_dir=str(temp_prompts_dir))
        
        categories = manager.list_categories()
        
        assert len(categories) == 2
        assert "social" in categories
        assert "professional" in categories
    
    def test_get_category_info(self, temp_prompts_dir):
        """Test getting category metadata."""
        manager = PromptManager(prompts_dir=str(temp_prompts_dir))
        
        social_info = manager.get_category_info("social")
        
        assert social_info["description"] == "Social interactions"
        assert social_info["file"] == "social.yaml"
    
    def test_validate_prompt_success(self, temp_prompts_dir):
        """Test successful prompt validation."""
        manager = PromptManager(prompts_dir=str(temp_prompts_dir))
        
        # Valid variables
        assert manager.validate_prompt("social", name="Alice", message="Hello")
        
        # Missing variables
        assert not manager.validate_prompt("social", name="Alice")  # Missing message
    
    def test_prompt_formatting_integration(self, temp_prompts_dir):
        """Test full integration of getting and formatting prompts."""
        manager = PromptManager(prompts_dir=str(temp_prompts_dir))
        
        social_prompt = manager.get_prompt("social")
        formatted = social_prompt.format(name="Alice", message="How are you?")
        
        assert "Social interaction: Alice" in formatted
        assert "Message: How are you?" in formatted
    
    def test_config_file_not_found(self, temp_prompts_dir):
        """Test error when config file is missing."""
        # Remove config file
        (temp_prompts_dir / "config.yaml").unlink()
        
        with pytest.raises(PromptManagerError, match="Config file not found"):
            PromptManager(prompts_dir=str(temp_prompts_dir))
    
    def test_prompt_file_not_found(self, temp_prompts_dir):
        """Test error when prompt file is missing."""
        # Remove social.yaml file
        (temp_prompts_dir / "social.yaml").unlink()
        
        # This should fail during initialization because it tries to reload all prompts
        with pytest.raises(PromptManagerError, match="Failed to reload prompts"):
            PromptManager(prompts_dir=str(temp_prompts_dir))
    
    @patch('app.services.prompt_manager.os.path.getmtime')
    def test_hot_reload_detection(self, mock_getmtime, temp_prompts_dir):
        """Test hot reload file modification detection."""
        # Mock file modification times - need more values for all the getmtime calls
        mock_getmtime.return_value = 1000  # Initial loading
        
        with patch.object(PromptManager, '_is_hot_reload_enabled', return_value=True):
            manager = PromptManager(prompts_dir=str(temp_prompts_dir))
            
            # First call - loads from cache
            prompt1 = manager.get_prompt("social")
            
            # Change the mock to return newer time for reload detection
            mock_getmtime.return_value = 1001
            
            # Second call - should trigger reload due to newer mtime
            with patch.object(manager, '_load_prompt_file') as mock_load:
                mock_load.return_value = prompt1
                prompt2 = manager.get_prompt("social")
                mock_load.assert_called_once()
    
    def test_reload_prompts_manually(self, temp_prompts_dir):
        """Test manual prompt reloading."""
        manager = PromptManager(prompts_dir=str(temp_prompts_dir))
        
        # Clear cache to test reload
        manager._prompt_cache.clear()
        
        # Reload should populate cache again
        manager.reload_prompts()
        
        assert len(manager._prompt_cache) == 2
        assert "social" in manager._prompt_cache
        assert "professional" in manager._prompt_cache


@pytest.mark.unit  
class TestPromptManagerError:
    """Test PromptManagerError exception class."""
    
    def test_prompt_manager_error_creation(self):
        """Test creating PromptManagerError with message."""
        error = PromptManagerError("Test error message")
        assert str(error) == "Test error message"
    
    def test_prompt_manager_error_inheritance(self):
        """Test that PromptManagerError inherits from Exception."""
        error = PromptManagerError("Test")
        assert isinstance(error, Exception)