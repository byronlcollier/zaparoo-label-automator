"""
Endpoint Configuration Manager

This module handles loading and processing the API endpoints configuration
from the JSON configuration file, automatically appending limit statements to queries.
"""

import json
import os
from typing import List, Dict, Any


class ConfigManager:
    """
    Manages the endpoint configuration from the pure JSON configuration file.

    This class handles:
    - Loading the JSON configuration file
    - Automatically appending limit statements to query bodies
    - Providing access to processed endpoint configurations
    """

    def __init__(self, config_file_path: str):
        """
        Initialize the endpoint configuration manager.

        Args:
            config_file_path: Path to the endpoints configuration file
        """
        self.config_file_path = config_file_path
        self.endpoints = []

    def load_endpoints(self, batch_limit: int) -> List[Dict[str, Any]]:
        """
        Load and process the endpoints configuration file.

        Args:
            batch_limit: The batch limit value to append to query bodies

        Returns:
            List of endpoint configurations with limit statements appended

        Raises:
            FileNotFoundError: If the configuration file doesn't exist
            json.JSONDecodeError: If the file is not valid JSON
        """
        # Check if file exists
        if not os.path.exists(self.config_file_path):
            raise FileNotFoundError(f"Configuration file not found: {self.config_file_path}")

        # Read the JSON file directly
        with open(self.config_file_path, 'r', encoding='utf-8') as f:
            try:
                self.endpoints = json.load(f)
            except json.JSONDecodeError as e:
                raise json.JSONDecodeError(
                    f"Invalid JSON in configuration file: {str(e)}",
                    f.read(),
                    e.pos
                )

        # Process each endpoint to append limit statements
        processed_endpoints = []
        for endpoint in self.endpoints:
            processed_endpoint = self._append_limit_to_endpoint(endpoint, batch_limit)
            processed_endpoints.append(processed_endpoint)

        self.endpoints = processed_endpoints
        return self.endpoints

    def _append_limit_to_endpoint(self, endpoint: Dict[str, Any], batch_limit: int) -> Dict[str, Any]:
        """
        Append a limit statement to the body field of an endpoint configuration.

        Args:
            endpoint: The endpoint configuration dictionary
            batch_limit: The limit value to append

        Returns:
            Modified endpoint configuration with limit appended to body
        """
        # Create a copy to avoid modifying the original
        modified_endpoint = endpoint.copy()

        if 'properties' in modified_endpoint and 'body' in modified_endpoint['properties']:
            # Create a copy of properties to avoid modifying the original
            modified_endpoint['properties'] = modified_endpoint['properties'].copy()

            body = modified_endpoint['properties']['body']

            # Ensure the body ends with a semicolon, then append the limit
            if not body.endswith(';'):
                body += ';'

            # Append the limit statement with semicolon termination
            body += f" limit {batch_limit};"

            modified_endpoint['properties']['body'] = body

        return modified_endpoint

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
