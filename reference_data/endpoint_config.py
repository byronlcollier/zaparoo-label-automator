"""
Endpoint Configuration Manager

This module handles loading and processing the API endpoints configuration
from the Jinja template file, substituting variables at runtime.
"""

import json
import os
from typing import List, Dict, Any


class ConfigManager:
    """
    Manages the endpoint configuration from the api_endpoints.json.j2 file.
    
    This class handles:
    - Loading the Jinja template file
    - Substituting template variables
    - Providing access to endpoint configurations
    """
    
    def __init__(self, config_file_path: str = "api_endpoints.json.j2"):
        """
        Initialize the endpoint configuration manager.
        
        Args:
            config_file_path: Path to the endpoints configuration file
        """
        self.config_file_path = config_file_path
        self.endpoints = []
        
    def load_endpoints(self, template_variables: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Load and process the endpoints configuration file.
        
        Args:
            template_variables: Dictionary of variables to substitute in the template
            
        Returns:
            List of endpoint configurations
            
        Raises:
            FileNotFoundError: If the configuration file doesn't exist
            json.JSONDecodeError: If the file is not valid JSON after template processing
        """
        if template_variables is None:
            template_variables = {}
        
        # Check if file exists
        if not os.path.exists(self.config_file_path):
            raise FileNotFoundError(f"Configuration file not found: {self.config_file_path}")
        
        # Read the template file
        with open(self.config_file_path, 'r', encoding='utf-8') as f:
            template_content = f.read()
        
        # Process template variables (simple string replacement)
        processed_content = self._substitute_template_variables(template_content, template_variables)
        
        # Parse JSON
        try:
            self.endpoints = json.loads(processed_content)
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(
                f"Invalid JSON in configuration file after template processing: {str(e)}",
                processed_content,
                e.pos
            )
        
        return self.endpoints
    
    def _substitute_template_variables(self, content: str, variables: Dict[str, Any]) -> str:
        """
        Substitute Jinja-style template variables in the content.
        
        This is a simple implementation that replaces {{variable_name}} patterns
        with their corresponding values from the variables dictionary.
        
        Args:
            content: The template content
            variables: Dictionary of variable names to values
            
        Returns:
            Content with variables substituted
        """
        result = content
        
        for var_name, var_value in variables.items():
            placeholder = f"{{{{{var_name}}}}}"
            result = result.replace(placeholder, str(var_value))
        
        return result
    
    def get_endpoints(self) -> List[Dict[str, Any]]:
        """
        Get the loaded endpoints configuration.
        
        Returns:
            List of endpoint configurations
        """
        return self.endpoints
    
    def get_endpoint_by_name(self, name: str) -> Dict[str, Any]:
        """
        Get a specific endpoint configuration by name.
        
        Args:
            name: The name of the endpoint to retrieve
            
        Returns:
            Endpoint configuration dictionary
            
        Raises:
            ValueError: If endpoint with given name is not found
        """
        for endpoint in self.endpoints:
            if endpoint.get('name') == name:
                return endpoint
        
        raise ValueError(f"Endpoint '{name}' not found in configuration")
    
    def validate_endpoint_config(self, endpoint: Dict[str, Any]) -> bool:
        """
        Validate that an endpoint configuration has all required fields.
        
        Args:
            endpoint: Endpoint configuration dictionary
            
        Returns:
            True if valid, False otherwise
        """
        required_fields = ['name', 'properties']
        required_properties = ['endpoint_url', 'http_method', 'body']
        
        # Check top-level required fields
        for field in required_fields:
            if field not in endpoint:
                return False
        
        # Check required properties
        properties = endpoint.get('properties', {})
        for prop in required_properties:
            if prop not in properties:
                return False
        
        return True