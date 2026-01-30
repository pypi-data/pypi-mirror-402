from pathlib import Path

from builders_hut.setups import file_contents

FILES_TO_WRITE: dict[Path, str] = {
    # Main
    Path("app/main.py"): file_contents.APP_MAIN_CONTENT,
    # API
    Path("app/api/__init__.py"): file_contents.APP_API_INIT_CONTENT,
    Path("app/api/common.py"): file_contents.APP_API_COMMON_CONTENT,
    Path("app/api/v1/__init__.py"): file_contents.APP_API_V1_INIT_CONTENT,
    Path("app/api/v1/hero.py"): file_contents.APP_API_V1_HERO_CONTENT,
    # Core
    Path("app/core/__init__.py"): file_contents.APP_CORE_INIT_CONTENT,
    Path("app/core/config.py"): file_contents.APP_CORE_CONFIG_CONTENT,
    Path("app/core/lifespan.py"): file_contents.APP_CORE_LIFESPAN_CONTENT,
    # Models
    Path("app/models/__init__.py"): file_contents.APP_MODELS_INIT_CONTENT,
    Path("app/models/hero.py"): file_contents.APP_MODELS_HERO_CONTENT,
    Path("app/models/common.py"): file_contents.APP_MODELS_COMMON_CONTENT,
    # Repositories
    Path("app/repositories/__init__.py"): file_contents.APP_REPO_INIT_CONTENT_FOR_SQL,
    Path("app/repositories/hero.py"): file_contents.APP_REPO_HERO_CONTENT_FOR_SQL,
    # Services
    Path("app/services/__init__.py"): file_contents.APP_SERVICE_INIT_CONTENT,
    Path("app/services/hero.py"): file_contents.APP_SERVICE_HERO_CONTENT,
    # Templates
    Path("app/templates/index.html"): file_contents.APP_TEMPLATES_INDEX_CONTENT,
    # Utils
    Path("app/utils/__init__.py"): file_contents.APP_UTILS_INIT_CONTENT,
    Path("app/utils/common.py"): file_contents.APP_UTILS_COMMON_CONTENT,
    # .env Files
    Path(".env"): file_contents.ENV_FILE_CONTENT,
    # .gitignore File
    Path(".gitignore"): file_contents.GIT_IGNORE_FILE_CONTENT,
    # run.py
    Path("run.py"): file_contents.RU_FILE_CONTENT,
}
