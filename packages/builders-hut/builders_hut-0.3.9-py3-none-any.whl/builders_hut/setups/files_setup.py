from builders_hut.setups import BaseSetup
from builders_hut.utils import make_file


class SetupFiles(BaseSetup):
    """
    Create all the required files for the project.
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
        "app/schemas/__init__.py",
        "app/services/__init__.py",
        "app/repositories/__init__.py",
        "app/utils/__init__.py",
        "app/database/__init__.py",
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
            make_file(full_path)
