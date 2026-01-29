from .app_main import APP_MAIN_CONTENT
from .app_api import APP_API_INIT_CONTENT, APP_API_COMMON_CONTENT
from .app_core import (
    APP_CORE_INIT_CONTENT,
    APP_CORE_CONFIG_CONTENT,
    APP_CORE_LIFESPAN_CONTENT,
)
from .app_database import APP_DATABASE_SESSION_CONTENT_FOR_SQL
from .app_model import APP_MODELS_COMMON_CONTENT
from .app_scripts import APP_SCRIPTS_DEV_CONTENT
from .app_templates import APP_TEMPLATES_INDEX_CONTENT


from .env_file import ENV_FILE_CONTENT
from .gitignore_file import GIT_IGNORE_FILE_CONTENT


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
    # Scripts
    APP_SCRIPTS_DEV_CONTENT,
    # Templates
    APP_TEMPLATES_INDEX_CONTENT,
    # .env File
    ENV_FILE_CONTENT,
    # .gitignore File
    GIT_IGNORE_FILE_CONTENT,
]
