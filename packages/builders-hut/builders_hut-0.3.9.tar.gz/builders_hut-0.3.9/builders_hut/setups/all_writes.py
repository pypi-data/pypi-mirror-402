from pathlib import Path

from builders_hut.setups import file_contents

FILES_TO_WRITE: dict[Path, str] = {
    # Main
    Path("app/main.py"): file_contents.APP_MAIN_CONTENT,
    # API
    Path("app/api/__init__.py"): file_contents.APP_API_INIT_CONTENT,
    Path("app/api/common.py"): file_contents.APP_API_COMMON_CONTENT,
    # Core
    Path("app/core/__init__.py"): file_contents.APP_CORE_INIT_CONTENT,
    Path("app/core/config.py"): file_contents.APP_CORE_CONFIG_CONTENT,
    Path("app/core/lifespan.py"): file_contents.APP_CORE_LIFESPAN_CONTENT,
    # Scripts
    Path("app/scripts/dev.py"): file_contents.APP_SCRIPTS_DEV_CONTENT,
    # Templates
    Path("app/templates/index.html"): file_contents.APP_TEMPLATES_INDEX_CONTENT,
    # .env Files
    Path(".env"): file_contents.ENV_FILE_CONTENT,
    # .gitignore File
    Path(".gitignore"): file_contents.GIT_IGNORE_FILE_CONTENT,
}
