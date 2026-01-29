from rich import print

from builders_hut.setups import BaseSetup


class SetupFiles(BaseSetup):
    """
    Setup all the required files for the project.

        Structure:
    .
    ├── app
    │   ├── api             # API route definitions
    |   |   ├── __init__.py # init file
    │   ├── core            # Core configuration and application settings
    |   |   ├── __init__.py # init file
    |   |   ├── config.py   # Project Configurations
    |   |   ├── logger.py   # Logger
    │   ├── database        # Database setup, connections, and sessions
    |   |   ├── __init__.py # init file
    │   ├── models          # ORM / data models
    |   |   ├── __init__.py # init file
    │   ├── repositories    # Data access layer
    |   |   ├── __init__.py # init file
    │   ├── schemas         # Request and response schemas
    |   |   ├── __init__.py # init file
    │   ├── services        # Business logic
    |   |   ├── __init__.py # init file
    │   ├── utils           # Utility and helper functions
    |   |   ├── __init__.py # init file
    │   ├── workers         # Background jobs and async workers
    |   |   ├── __init__.py # init file
    |   ├── templates       # Static html for home page
    |   |   ├── index.html  # Html file
    │   └── main.py         # Application entry point
    │
    ├── tests               # Unit and integration tests
    |   ├── __init__.py     # init file
    ├── scripts             # Utility and automation scripts
    |   ├── __init__.py     # init file
    |   ├── dev.py          # Run server in dev mode
    |   ├── prod.py         # Run server in prod mode
    """

    FILES_TO_CREATE = [
        # Main application file
        "app/main.py",
        # Core configuration and logger files
        "app/core/config.py",
        "app/core/logger.py",
        "app/core/lifespan.py",
        "app/core/__init__.py",
        # __init__.py files for package initialization
        "app/models/__init__.py",
        "app/models/common.py",
        "app/schemas/__init__.py",
        "app/services/__init__.py",
        "app/repositories/__init__.py",
        "app/utils/__init__.py",
        "app/database/__init__.py",
        "app/database/session.py",
        "app/workers/__init__.py",
        "app/api/__init__.py",
        "app/api/v1/__init__.py",
        "app/api/common.py",
        "app/templates/index.html",
        # Test initialization file
        "tests/__init__.py",
        # Script files
        "app/scripts/dev.py",
        "app/scripts/prod.py",
        # Configuration
        "pyproject.toml",
        ".env",
        ".gitignore",
    ]

    def create(self):
        for file_path in self.FILES_TO_CREATE:
            full_path = self.location / file_path
            full_path.touch(exist_ok=True)
            print(f"Created file: [bold green]{file_path.split('/')[-1]}[/bold green]")
