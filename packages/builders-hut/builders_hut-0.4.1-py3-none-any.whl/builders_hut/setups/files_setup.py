from builders_hut.setups import BaseSetup
from builders_hut.utils import make_file


class SetupFiles(BaseSetup):
    """
    Create all the required files for the project.
    """

    FILES_TO_CREATE = [
        # Main application file
        "app/main.py",
        # api files
        "app/api/__init__.py",
        "app/api/common.py",
        "app/api/v1/__init__.py",
        "app/api/v1/hero.py",
        # Core configuration and logger files
        "app/core/__init__.py",
        "app/core/config.py",
        "app/core/lifespan.py",
        "app/core/logger.py",
        # database files
        "app/database/__init__.py",
        "app/database/session.py",
        # Model files
        "app/models/__init__.py",
        "app/models/common.py",
        "app/models/hero.py",
        # Repository files
        "app/repositories/__init__.py",
        "app/repositories/hero.py",
        # Schema files
        "app/schemas/__init__.py",
        # Service files
        "app/services/__init__.py",
        "app/services/hero.py",
        # templates files
        "app/templates/index.html",
        # Utils files
        "app/utils/__init__.py",
        "app/utils/common.py",
        # Workers files
        "app/workers/__init__.py",
        # Test initialization file
        "tests/__init__.py",
        # Configuration
        ".env",
        ".gitignore",
        "requirements.txt",
        "requirements_dev.txt",
        "run.py",
    ]

    def create(self):
        for file_path in self.FILES_TO_CREATE:
            full_path = self.location / file_path
            make_file(full_path)
