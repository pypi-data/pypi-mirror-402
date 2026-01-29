"""
Variable management for .http files.
Supports environment variables, file variables, and dynamic variables.
"""

import os
import re
import uuid
import random
import string
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml
from dotenv import dotenv_values


class VariableManager:
    """Manages variables from multiple sources."""
    
    # Pattern for variable references: {{variable_name}}
    VAR_PATTERN = re.compile(r'\{\{([^}]+)\}\}')
    
    # Built-in dynamic variables
    DYNAMIC_VARS = {
        '$uuid': lambda: str(uuid.uuid4()),
        '$guid': lambda: str(uuid.uuid4()),
        '$timestamp': lambda: str(int(datetime.now(timezone.utc).timestamp())),
        '$isoTimestamp': lambda: datetime.now(timezone.utc).isoformat(),
        '$randomInt': lambda: str(random.randint(0, 1000)),
        '$randomString': lambda: ''.join(random.choices(string.ascii_letters, k=10)),
    }
    
    def __init__(self):
        self._variables: dict[str, str] = {}
        self._env_file: dict[str, str] = {}
        
    def load_env_file(self, path: str | Path) -> None:
        """Load variables from a .env file."""
        path = Path(path)
        if path.exists():
            self._env_file.update(dotenv_values(path))
    
    def load_http_client_env(self, path: str | Path, environment: str = "dev") -> None:
        """Load variables from http-client.env.json (VS Code REST Client format)."""
        path = Path(path)
        if not path.exists():
            return
            
        with open(path) as f:
            data = yaml.safe_load(f)  # Works for JSON too
            
        if not isinstance(data, dict):
            return
            
        # Load common/shared variables first
        if "$shared" in data:
            self._variables.update(data["$shared"])
            
        # Load environment-specific variables
        if environment in data:
            self._variables.update(data[environment])
    
    def set(self, name: str, value: str) -> None:
        """Set a variable."""
        self._variables[name] = value
    
    def set_many(self, variables: dict[str, str]) -> None:
        """Set multiple variables."""
        self._variables.update(variables)
    
    def get(self, name: str) -> str | None:
        """Get a variable value. Priority: file vars > env file > env vars > dynamic."""
        # Check file variables first
        if name in self._variables:
            return self._variables[name]
        
        # Check .env file
        if name in self._env_file:
            return self._env_file[name]
        
        # Check environment variables
        if name in os.environ:
            return os.environ[name]
        
        # Check dynamic variables
        if name in self.DYNAMIC_VARS:
            return self.DYNAMIC_VARS[name]()
        
        return None
    
    def resolve(self, text: str) -> str:
        """Resolve all variable references in a string."""
        def replace_var(match: re.Match) -> str:
            var_name = match.group(1).strip()
            value = self.get(var_name)
            if value is None:
                # Keep original if variable not found
                return match.group(0)
            return value
        
        return self.VAR_PATTERN.sub(replace_var, text)
    
    def get_all(self) -> dict[str, str]:
        """Get all defined variables."""
        result = {}
        result.update(self._env_file)
        result.update(self._variables)
        return result
