"""Main logger implementation for dbt projects."""

import subprocess
import sys
from datetime import datetime
from typing import Optional, Dict, Any
import snowflake.connector
from .utils import get_connection_params_from_dbt, get_logger_config


class DbtLogger:
    """A logger that captures dbt command output and logs to Snowflake."""
    
    def __init__(
        self,
        repo_name: str,
        connection_params: Optional[Dict[str, Any]] = None,
        profile_name: Optional[str] = None,
        target: Optional[str] = None,
        table_name: Optional[str] = None,
        schema: Optional[str] = None,
        database: Optional[str] = None
    ):
        """
        Initialize the DbtLogger.
        
        Args:
            repo_name: Name of the dbt project/repo
            connection_params: Snowflake connection parameters (if None, reads from dbt profiles.yml)
            profile_name: dbt profile name (only used if connection_params is None)
            target: dbt target name like 'dev' or 'prod' (only used if connection_params is None)
            table_name: Name of the logging table (overrides config file)
            schema: Schema name (overrides config file)
            database: Database name (overrides config file)
        """
        self.repo_name = repo_name
        
        # Get connection params from dbt profiles if not provided
        if connection_params is None:
            connection_params = get_connection_params_from_dbt(
                profile_name=profile_name,
                target=target
            )
        
        self.connection_params = connection_params
        
        # Load config file settings
        config = get_logger_config()
        
        # Determine database, schema, and table name with precedence:
        # 1. Explicit parameter
        # 2. Config file
        # 3. Defaults
        dbt_database = connection_params.get('database')
        
        self.database = database or config.get('database') or dbt_database
        self.schema = schema or config.get('schema') or "logging"
        self.table_name = table_name or config.get('table_name') or "dbt_logging"
        
        self.full_table_name = f"{self.database}.{self.schema}.{self.table_name}"
        
        # Ensure the logging table exists
        self._ensure_table_exists()
    
    def _get_connection(self):
        """Get a Snowflake connection."""
        return snowflake.connector.connect(**self.connection_params)
    
    def _ensure_table_exists(self):
        """Create the logging schema and table if they don't exist."""
        create_schema_sql = f"CREATE SCHEMA IF NOT EXISTS {self.database}.{self.schema}"
        
        create_table_sql = f"""
        CREATE TABLE IF NOT EXISTS {self.full_table_name} (
            repo_name STRING,
            command STRING,
            stdout_log STRING,
            log_time TIMESTAMP_LTZ DEFAULT CURRENT_TIMESTAMP()
        )
        """
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(create_schema_sql)
            cursor.execute(create_table_sql)
            cursor.close()
            conn.close()
        except Exception as e:
            print(f"Warning: Could not create logging table: {e}")
    
    def run_command(self, command: str) -> int:
        """
        Run a dbt command and log its output to Snowflake.
        
        Args:
            command: The full dbt command to run (e.g., "dbt build", "dbt run --select model_name")
        
        Returns:
            Exit code of the command
        """
        print(f"Running: {command}")
        print("=" * 60)
        
        # Run the command and capture output
        try:
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            output_lines = []
            for line in process.stdout:
                # Print in real-time
                print(line, end='')
                output_lines.append(line)
            
            process.wait()
            exit_code = process.returncode
            
            # Combine all output
            full_output = ''.join(output_lines)
            
            # Log to Snowflake
            self._log_to_snowflake(command, full_output)
            
            print("=" * 60)
            print(f"Command completed with exit code: {exit_code}")
            
            return exit_code
            
        except Exception as e:
            error_msg = f"Error running command: {e}"
            print(error_msg)
            self._log_to_snowflake(command, error_msg)
            return 1
    
    def _log_to_snowflake(self, command: str, stdout_log: str):
        """Insert the command and output into Snowflake."""
        insert_sql = f"""
        INSERT INTO {self.full_table_name} (repo_name, command, stdout_log, log_time)
        VALUES (%s, %s, %s, %s)
        """
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                insert_sql,
                (self.repo_name, command, stdout_log, datetime.now())
            )
            conn.commit()
            cursor.close()
            conn.close()
        except Exception as e:
            print(f"Warning: Could not log to Snowflake: {e}")
