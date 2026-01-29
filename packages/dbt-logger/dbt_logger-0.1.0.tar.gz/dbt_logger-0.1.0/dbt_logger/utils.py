"""Utility functions for dbt-logger."""

from typing import Dict, Any, Optional
import os
import yaml
import re
from pathlib import Path


def get_logger_config() -> Dict[str, Any]:
    """
    Load configuration from dbt/dbt_logger.yml if it exists.
    
    Returns:
        Dictionary with optional keys: database, schema, table_name
    """
    config_paths = [
        Path.cwd() / 'dbt' / 'dbt_logger.yml',
        Path.cwd() / 'dbt_logger.yml',
    ]
    
    for config_path in config_paths:
        if config_path.exists():
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f) or {}
                return config
    
    return {}


def _resolve_env_var(value: str) -> str:
    """
    Resolve Jinja-style environment variable references.
    
    Handles patterns like {{ env_var('VAR_NAME') }}
    """
    if not isinstance(value, str):
        return value
    
    # Match {{ env_var('VAR_NAME') }} or {{ env_var("VAR_NAME") }}
    pattern = r"{{\s*env_var\(['\"]([^'\"]+)['\"]\)\s*}}"
    
    def replacer(match):
        env_var_name = match.group(1)
        env_value = os.getenv(env_var_name)
        if env_value is None:
            raise ValueError(f"Environment variable '{env_var_name}' is not set")
        return env_value
    
    return re.sub(pattern, replacer, value)


def get_dbt_profile_path() -> Path:
    """
    Get the path to the dbt profiles.yml file.
    
    Checks in order:
    1. DBT_PROFILES_DIR environment variable
    2. Current directory ./dbt/profiles/profiles.yml
    3. ~/.dbt/profiles.yml (default location)
    """
    # Check environment variable
    profiles_dir = os.getenv('DBT_PROFILES_DIR')
    if profiles_dir:
        profiles_path = Path(profiles_dir) / 'profiles.yml'
        if profiles_path.exists():
            return profiles_path
    
    # Check local dbt/profiles directory
    local_path = Path.cwd() / 'dbt' / 'profiles' / 'profiles.yml'
    if local_path.exists():
        return local_path
    
    # Check default home directory
    home_path = Path.home() / '.dbt' / 'profiles.yml'
    if home_path.exists():
        return home_path
    
    raise FileNotFoundError(
        "Could not find profiles.yml. Checked:\n"
        f"  - $DBT_PROFILES_DIR/profiles.yml\n"
        f"  - {local_path}\n"
        f"  - {home_path}"
    )


def get_connection_params_from_dbt(
    profile_name: Optional[str] = None,
    target: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get Snowflake connection parameters from dbt profiles.yml.
    
    Args:
        profile_name: Name of the profile in profiles.yml (if None, uses DBT_PROFILE env var or first profile)
        target: Target name (dev/prod) (if None, uses profile's default target)
    
    Returns:
        Dictionary of connection parameters suitable for snowflake.connector.connect()
    """
    profiles_path = get_dbt_profile_path()
    
    with open(profiles_path, 'r') as f:
        profiles = yaml.safe_load(f)
    
    # Determine which profile to use
    if profile_name is None:
        profile_name = os.getenv('DBT_PROFILE')
    
    if profile_name is None:
        # Use the first profile (excluding 'config' key if present)
        available_profiles = [k for k in profiles.keys() if k != 'config']
        if not available_profiles:
            raise ValueError("No profiles found in profiles.yml")
        profile_name = available_profiles[0]
    
    if profile_name not in profiles:
        raise ValueError(f"Profile '{profile_name}' not found in profiles.yml")
    
    profile = profiles[profile_name]
    
    # Determine which target to use
    if target is None:
        target = profile.get('target')
    
    if target is None:
        raise ValueError(f"No target specified and profile '{profile_name}' has no default target")
    
    if target not in profile.get('outputs', {}):
        raise ValueError(f"Target '{target}' not found in profile '{profile_name}'")
    
    output = profile['outputs'][target]
    
    # Resolve environment variables in the output
    resolved_output = {}
    for key, value in output.items():
        if isinstance(value, str):
            resolved_output[key] = _resolve_env_var(value)
        else:
            resolved_output[key] = value
    
    # Build connection parameters for Snowflake
    params = {
        'account': resolved_output.get('account'),
        'user': resolved_output.get('user'),
        'warehouse': resolved_output.get('warehouse'),
        'database': resolved_output.get('database'),
    }
    
    # Handle authentication - private key or password
    if 'private_key_path' in resolved_output:
        # Private key authentication
        private_key_path = resolved_output['private_key_path']
        private_key_passphrase = resolved_output.get('private_key_passphrase')
        
        # Read and parse the private key
        from cryptography.hazmat.backends import default_backend
        from cryptography.hazmat.primitives import serialization
        
        with open(private_key_path, 'rb') as key_file:
            private_key_data = key_file.read()
        
        passphrase = private_key_passphrase.encode() if private_key_passphrase else None
        
        private_key = serialization.load_pem_private_key(
            private_key_data,
            password=passphrase,
            backend=default_backend()
        )
        
        pkb = private_key.private_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        params['private_key'] = pkb
    elif 'password' in resolved_output:
        params['password'] = resolved_output['password']
    else:
        raise ValueError("No authentication method found (private_key_path or password)")
    
    # Optional parameters
    if 'role' in resolved_output:
        params['role'] = resolved_output['role']
    
    if 'schema' in resolved_output:
        params['schema'] = resolved_output['schema']
    
    return params


def get_connection_params_from_env() -> Dict[str, Any]:
    """
    Get Snowflake connection parameters from environment variables.
    
    Expected environment variables:
    - SNOWFLAKE_ACCOUNT
    - SNOWFLAKE_USER
    - SNOWFLAKE_PASSWORD
    - SNOWFLAKE_DATABASE
    - SNOWFLAKE_WAREHOUSE
    - SNOWFLAKE_ROLE (optional)
    
    Returns:
        Dictionary of connection parameters
    """
    params = {
        'account': os.getenv('SNOWFLAKE_ACCOUNT'),
        'user': os.getenv('SNOWFLAKE_USER'),
        'password': os.getenv('SNOWFLAKE_PASSWORD'),
        'database': os.getenv('SNOWFLAKE_DATABASE'),
        'warehouse': os.getenv('SNOWFLAKE_WAREHOUSE'),
    }
    
    role = os.getenv('SNOWFLAKE_ROLE')
    if role:
        params['role'] = role
    
    # Validate required parameters
    missing = [k for k, v in params.items() if v is None and k != 'role']
    if missing:
        raise ValueError(f"Missing required environment variables: {', '.join(f'SNOWFLAKE_{k.upper()}' for k in missing)}")
    
    return params