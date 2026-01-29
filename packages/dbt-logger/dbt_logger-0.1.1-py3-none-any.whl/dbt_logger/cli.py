"""CLI interface for dbt-logger."""

import argparse
import sys
from typing import Optional
from .utils import get_connection_params_from_dbt, get_logger_config, get_dbt_profile_path
from .logger import DbtLogger


def show_config(repo_name: str, target: Optional[str] = None):
    """Show the current configuration and where logs will be written."""
    print("=" * 60)
    print("dbt-logger Configuration")
    print("=" * 60)
    
    try:
        # Find profiles.yml
        profiles_path = get_dbt_profile_path()
        print(f"✓ profiles.yml: {profiles_path}")
        
        # Get connection params
        connection_params = get_connection_params_from_dbt(target=target)
        dbt_database = connection_params.get('database')
        print(f"✓ dbt database: {dbt_database}")
        print(f"✓ target: {target or 'default'}")
        
        # Get logger config
        config = get_logger_config()
        if config:
            print(f"✓ Config file found with: {config}")
        else:
            print("  No dbt_logger.yml config file found (using defaults)")
        
        # Determine final logging location
        database = config.get('database') or dbt_database
        schema = config.get('schema') or "logging"
        table_name = config.get('table_name') or "dbt_logging"
        
        print("\n" + "=" * 60)
        print("Logs will be written to:")
        print("=" * 60)
        print(f"  Database:   {database}")
        print(f"  Schema:     {schema}")
        print(f"  Table:      {table_name}")
        print(f"  Full path:  {database}.{schema}.{table_name}")
        print("=" * 60)
        
    except Exception as e:
        print(f"✗ Error: {e}", file=sys.stderr)
        sys.exit(1)


def test_connection(repo_name: str, target: Optional[str] = None):
    """Test the Snowflake connection."""
    print("=" * 60)
    print("Testing Snowflake Connection")
    print("=" * 60)
    
    try:
        connection_params = get_connection_params_from_dbt(target=target)
        print(f"✓ Loaded credentials for target: {target or 'default'}")
        
        # Try to create logger (this will test connection)
        logger = DbtLogger(repo_name=repo_name, target=target)
        print(f"✓ Connected to Snowflake")
        print(f"✓ Verified/created: {logger.full_table_name}")
        print("\n" + "=" * 60)
        print("Connection test PASSED ✓")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ Connection test FAILED", file=sys.stderr)
        print(f"✗ Error: {e}", file=sys.stderr)
        print("=" * 60)
        sys.exit(1)


def run_test_command(repo_name: str, target: Optional[str] = None):
    """Run a test dbt command and log it."""
    print("=" * 60)
    print("Running Test Command")
    print("=" * 60)
    
    try:
        logger = DbtLogger(repo_name=repo_name, target=target)
        print(f"Logging to: {logger.full_table_name}\n")
        
        # Run a simple dbt command
        exit_code = logger.run_command("dbt --version")
        
        if exit_code == 0:
            print("\n" + "=" * 60)
            print("Test PASSED ✓")
            print(f"Check {logger.full_table_name} for the logged output")
            print("=" * 60)
        else:
            print(f"\nCommand exited with code: {exit_code}")
            
    except Exception as e:
        print(f"✗ Error: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog='dbt-logger',
        description='Test and configure dbt-logger'
    )
    
    parser.add_argument(
        '--show-config',
        action='store_true',
        help='Show where logs will be written'
    )
    
    parser.add_argument(
        '--test-connection',
        action='store_true',
        help='Test the Snowflake connection'
    )
    
    parser.add_argument(
        '--test-run',
        action='store_true',
        help='Run a test command (dbt --version) and log it'
    )
    
    parser.add_argument(
        '--repo-name',
        default='test_repo',
        help='Repository name for testing (default: test_repo)'
    )
    
    parser.add_argument(
        '--target',
        help='dbt target to use (e.g., dev, prod)'
    )
    
    args = parser.parse_args()
    
    # If no action specified, show help
    if not any([args.show_config, args.test_connection, args.test_run]):
        parser.print_help()
        sys.exit(0)
    
    # Run requested actions
    if args.show_config:
        show_config(args.repo_name, args.target)
    
    if args.test_connection:
        test_connection(args.repo_name, args.target)
    
    if args.test_run:
        run_test_command(args.repo_name, args.target)


if __name__ == '__main__':
    main()
