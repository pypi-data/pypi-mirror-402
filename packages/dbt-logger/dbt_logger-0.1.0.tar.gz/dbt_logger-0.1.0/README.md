# dbt-logger

A logging utility that captures dbt command output and stores it in Snowflake for auditing and monitoring. **Uses your existing dbt credentials - no additional configuration needed!**

## Installation

```bash
pip install dbt-logger
```

## Quick Start

The simplest way - uses your existing dbt profiles.yml:

```python
from dbt_logger import DbtLogger

# Automatically uses credentials from dbt profiles.yml
logger = DbtLogger(repo_name="my_analytics_project")

# Run dbt commands and log them
logger.run_command("dbt build")
logger.run_command("dbt run --select +sales_model")
```

That's it! Logs are automatically saved to `[your_dbt_database].logging.dbt_logging`

## Configuration File (Optional)

Create `dbt/dbt_logger.yml` in your dbt project to configure logging destination:

```yaml
# dbt/dbt_logger.yml

# Option 1: Custom schema in dbt database
schema: audit_logs

# Option 2: Completely separate database for logs
database: ADMIN_DB
schema: LOGGING
table_name: dbt_execution_logs
```

**Precedence order:**
1. Parameters passed to `DbtLogger()` (highest)
2. Settings in `dbt/dbt_logger.yml`
3. Defaults: `{dbt_database}.logging.dbt_logging` (lowest)

## Configuration Options

### Use Specific dbt Profile/Target

```python
# Use a specific profile and target from profiles.yml
logger = DbtLogger(
    repo_name="my_project",
    profile_name="my_profile",  # Optional: defaults to first profile
    target="prod"                # Optional: defaults to profile's default target
)
```

### Override Logging Location in Code

```python
# Override config file settings
logger = DbtLogger(
    repo_name="my_project",
    database="ADMIN_DB",
    schema="LOGGING",
    table_name="my_custom_logs"
)
```

### Manual Connection Parameters (Advanced)

If you need to use different credentials than dbt:

```python
from dbt_logger import DbtLogger, get_connection_params_from_env

# Option 1: From environment variables
connection_params = get_connection_params_from_env()

# Option 2: Manual dict
connection_params = {
    'account': 'your_account',
    'user': 'your_user',
    'password': 'your_password',
    'database': 'your_database',
    'warehouse': 'your_warehouse',
}

logger = DbtLogger(
    repo_name="my_project",
    connection_params=connection_params
)
```

## How It Works

1. **Reads your dbt profiles.yml** - Automatically finds and parses your dbt configuration
2. **Supports private key auth** - Works with your existing DBT_USER, DBT_PVK_PATH, DBT_PVK_PASS env vars
3. **Creates logging infrastructure** - Auto-creates schema and table on first run
4. **Captures everything** - Runs dbt commands and logs all output in real-time
5. **Stores in Snowflake** - Saves command history for auditing and monitoring

## Logging Table Schema

```sql
-- Default location: [your_dbt_database].logging.dbt_logging
CREATE TABLE dbt_logging (
    repo_name STRING,      -- Your dbt project/repo name
    command STRING,        -- The dbt command executed
    stdout_log STRING,     -- Complete command output
    log_time TIMESTAMP_LTZ -- Execution timestamp
);
```

## dbt profiles.yml Locations

The logger checks for profiles.yml in this order:
1. `$DBT_PROFILES_DIR/profiles.yml`
2. `./dbt/profiles/profiles.yml` (current directory)
3. `~/.dbt/profiles.yml` (default dbt location)

## Features

- ✅ **Zero Config** - Uses your existing dbt credentials
- ✅ **Private Key Auth** - Full support for private key authentication
- ✅ **Auto Setup** - Creates schema and table automatically
- ✅ **Real-time Output** - See command output live while logging
- ✅ **Flexible Storage** - Default to dbt database or use separate logging database
- ✅ **Environment Variables** - Resolves Jinja env_var() expressions from profiles.yml

## License

MIT License - see LICENSE file for details.