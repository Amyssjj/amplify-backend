"""
Prompt management service for externalized AI prompts.
"""
import os
import time
from pathlib import Path
from typing import Dict, Any, Optional
import yaml
from pydantic import BaseModel, Field
from app.core.config import settings


class PromptTemplate(BaseModel):
    """Model for a loaded prompt template."""
    category: str
    name: str
    version: str
    description: str
    last_updated: str
    tags: list[str] = Field(default_factory=list)
    variables: list[str] = Field(default_factory=list)
    template: str
    
    def format(self, **kwargs) -> str:
        """Format the template with provided variables."""
        # Validate that all required variables are provided
        missing_vars = [var for var in self.variables if var not in kwargs]
        if missing_vars:
            raise ValueError(f"Missing required variables: {missing_vars}")
        
        return self.template.format(**kwargs)


class PromptManagerError(Exception):
    """Custom exception for prompt manager errors."""
    pass


class PromptManager:
    """Manages externalized AI prompts with hot-reload capability."""
    
    def __init__(self, prompts_dir: Optional[str] = None):
        """Initialize prompt manager."""
        self.prompts_dir = Path(prompts_dir or "app/prompts")
        self.config_file = self.prompts_dir / "config.yaml"
        
        # Cache for loaded prompts
        self._prompt_cache: Dict[str, PromptTemplate] = {}
        self._file_mtimes: Dict[str, float] = {}
        
        # Load configuration and prompts
        self._load_config()
        self.reload_prompts()
    
    def _load_config(self) -> None:
        """Load the global prompt configuration."""
        try:
            if not self.config_file.exists():
                raise PromptManagerError(f"Config file not found: {self.config_file}")
            
            with open(self.config_file, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
                
        except Exception as e:
            raise PromptManagerError(f"Failed to load config: {str(e)}")
    
    def _should_reload(self, category: str) -> bool:
        """Check if a category file should be reloaded based on modification time."""
        if not self._is_hot_reload_enabled():
            return False
        
        category_file = self._get_category_file_path(category)
        if not category_file.exists():
            return False
        
        current_mtime = os.path.getmtime(category_file)
        cached_mtime = self._file_mtimes.get(category, 0)
        
        return current_mtime > cached_mtime
    
    def _is_hot_reload_enabled(self) -> bool:
        """Check if hot reload is enabled."""
        # Check settings first, then config file, default to debug mode
        if hasattr(settings, 'prompts_hot_reload'):
            return settings.prompts_hot_reload
        
        return self.config.get('settings', {}).get('hot_reload_enabled', settings.debug)
    
    def _get_category_file_path(self, category: str) -> Path:
        """Get the file path for a category."""
        if category not in self.config.get('categories', {}):
            raise PromptManagerError(f"Unknown category: {category}")
        
        filename = self.config['categories'][category].get('file', f"{category}.yaml")
        return self.prompts_dir / filename
    
    def _load_prompt_file(self, category: str) -> PromptTemplate:
        """Load a single prompt file."""
        category_file = self._get_category_file_path(category)
        
        try:
            if not category_file.exists():
                raise PromptManagerError(f"Prompt file not found: {category_file}")
            
            with open(category_file, 'r', encoding='utf-8') as f:
                prompt_data = yaml.safe_load(f)
            
            # Validate the prompt data structure
            if not isinstance(prompt_data, dict):
                raise PromptManagerError(f"Invalid prompt file format: {category_file}")
            
            # Update file modification time
            self._file_mtimes[category] = os.path.getmtime(category_file)
            
            return PromptTemplate(**prompt_data)
            
        except Exception as e:
            raise PromptManagerError(f"Failed to load prompt file {category_file}: {str(e)}")
    
    def reload_prompts(self) -> None:
        """Reload all prompts from disk."""
        try:
            categories = self.config.get('categories', {})
            
            for category in categories.keys():
                prompt_template = self._load_prompt_file(category)
                self._prompt_cache[category] = prompt_template
                
        except Exception as e:
            raise PromptManagerError(f"Failed to reload prompts: {str(e)}")
    
    def get_prompt(self, category: str) -> PromptTemplate:
        """
        Get a prompt template by category.
        
        Args:
            category: The prompt category (e.g., 'social', 'professional')
            
        Returns:
            PromptTemplate: The loaded prompt template
            
        Raises:
            PromptManagerError: If category doesn't exist or loading fails
        """
        # Check if we need to reload due to file changes
        if self._should_reload(category):
            try:
                self._prompt_cache[category] = self._load_prompt_file(category)
            except Exception as e:
                # If reload fails, continue with cached version and log warning
                # In production, you might want to log this properly
                pass
        
        # Return from cache
        if category not in self._prompt_cache:
            # Try to load if not in cache
            self._prompt_cache[category] = self._load_prompt_file(category)
        
        return self._prompt_cache[category]
    
    def list_categories(self) -> list[str]:
        """List all available prompt categories."""
        return list(self.config.get('categories', {}).keys())
    
    def get_category_info(self, category: str) -> Dict[str, Any]:
        """Get metadata information about a category."""
        if category not in self.config.get('categories', {}):
            raise PromptManagerError(f"Unknown category: {category}")
        
        return self.config['categories'][category]
    
    def validate_prompt(self, category: str, **variables) -> bool:
        """
        Validate that all required variables are provided for a prompt.
        
        Args:
            category: The prompt category
            **variables: Variables to validate against the prompt
            
        Returns:
            bool: True if all required variables are present
        """
        try:
            prompt = self.get_prompt(category)
            missing_vars = [var for var in prompt.variables if var not in variables]
            return len(missing_vars) == 0
        except Exception:
            return False


# Global instance
prompt_manager = PromptManager()