"""Allow running dbt-logger as a module: python -m dbt_logger"""

from .cli import main

if __name__ == '__main__':
    main()
