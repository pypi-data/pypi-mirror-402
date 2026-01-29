from rich import print

from builders_hut.setups import BaseSetup


class SetupStructure(BaseSetup):
    """
    Setup all the required directory structure for the project.

    Structure:
    .
    ├── app
    │   ├── api           # API route definitions
    |   |   ├── v1        # Version 1 endpoints
    │   ├── core          # Core configuration and application settings
    │   ├── database      # Database setup, connections, and sessions
    │   ├── models        # ORM / data models
    │   ├── repositories  # Data access layer
    │   ├── schemas       # Request and response schemas
    │   ├── services      # Business logic
    │   ├── utils         # Utility and helper functions
    │   ├── workers       # Background jobs and async workers
    |   ├── scripts       # Utility and automation scripts to run server
    |   ├── templates     # Templates
    │
    ├── tests             # Unit and integration tests
    """

    ALL_DIRS = [
        "api",
        "api/v1",
        "database",
        "schemas",
        "services",
        "repositories",
        "core",
        "models",
        "workers",
        "utils",
        "scripts",
        "templates",
    ]

    def create(self):
        print(
            f"Creating directory structure at: [bold green]{self.location}[/bold green]"
        )
        (self.location / "tests").mkdir(exist_ok=True, parents=True)
        (self.location / "app").mkdir(exist_ok=True, parents=True)
        for dir_name in self.ALL_DIRS:
            (self.location / "app" / dir_name).mkdir(exist_ok=True, parents=True)
        print("All directories created [bold green]successfully![/bold green]")
