from .app_api import APP_API_COMMON_CONTENT, APP_API_INIT_CONTENT
from .app_api_v1 import APP_API_V1_HERO_CONTENT, APP_API_V1_INIT_CONTENT
from .app_core import (
    APP_CORE_CONFIG_CONTENT,
    APP_CORE_INIT_CONTENT,
    APP_CORE_LIFESPAN_CONTENT,
)
from .app_database import (
    APP_DATABASE_INIT_CONTENT_FOR_SQL,
    APP_DATABASE_SESSION_CONTENT_FOR_SQL,
)
from .app_main import APP_MAIN_CONTENT
from .app_model import (
    APP_MODELS_COMMON_CONTENT,
    APP_MODELS_HERO_CONTENT,
    APP_MODELS_INIT_CONTENT,
)
from .app_repository import APP_REPO_HERO_CONTENT_FOR_SQL, APP_REPO_INIT_CONTENT_FOR_SQL
from .app_services import APP_SERVICE_INIT_CONTENT, APP_SERVICE_HERO_CONTENT
from .app_templates import APP_TEMPLATES_INDEX_CONTENT
from .env_file import ENV_FILE_CONTENT
from .gitignore_file import GIT_IGNORE_FILE_CONTENT
from .migrations_env_file import MIGRATIONS_ENV_FILE_CONTENT
from .app_utils import APP_UTILS_COMMON_CONTENT, APP_UTILS_INIT_CONTENT
from .run_file import RU_FILE_CONTENT

__all__ = [
    # main
    APP_MAIN_CONTENT,
    # API
    APP_API_INIT_CONTENT,
    APP_API_COMMON_CONTENT,
    # Core
    APP_CORE_INIT_CONTENT,
    APP_CORE_CONFIG_CONTENT,
    APP_CORE_LIFESPAN_CONTENT,
    # Database
    APP_DATABASE_SESSION_CONTENT_FOR_SQL,
    # Model
    APP_MODELS_COMMON_CONTENT,
    # Templates
    APP_TEMPLATES_INDEX_CONTENT,
    # .env File
    ENV_FILE_CONTENT,
    # .gitignore File
    GIT_IGNORE_FILE_CONTENT,
    # alemmbic Migrations env file
    MIGRATIONS_ENV_FILE_CONTENT,
    # API v1
    APP_API_V1_INIT_CONTENT,
    APP_API_V1_HERO_CONTENT,
    # Database init
    APP_DATABASE_INIT_CONTENT_FOR_SQL,
    APP_DATABASE_INIT_CONTENT_FOR_SQL,
    # Model init
    APP_MODELS_HERO_CONTENT,
    APP_MODELS_INIT_CONTENT,
    # Repository
    APP_REPO_INIT_CONTENT_FOR_SQL,
    APP_REPO_HERO_CONTENT_FOR_SQL,
    # Services
    APP_SERVICE_INIT_CONTENT,
    APP_SERVICE_HERO_CONTENT,
    # Utils
    APP_UTILS_INIT_CONTENT,
    APP_UTILS_COMMON_CONTENT,
    RU_FILE_CONTENT,
]
