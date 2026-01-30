from typing import Literal
from builders_hut.utils import write_file, run_subprocess, get_python_file
from pathlib import Path
from builders_hut.setups.file_contents import (
    APP_DATABASE_SESSION_CONTENT_FOR_SQL,
    MIGRATIONS_ENV_FILE_CONTENT,
    APP_DATABASE_INIT_CONTENT_FOR_SQL,
)


class DatabaseFactory:
    def __init__(
        self,
        database_type: Literal["sql", "nosql"],
        location: Path,
    ):
        self.database_type = database_type
        self.location = location

    def setup_db(self):
        match self.database_type:
            case "sql":
                write_file(
                    self.location / "app" / "database" / "session.py",
                    APP_DATABASE_SESSION_CONTENT_FOR_SQL,
                )
                write_file(
                    self.location / "app" / "database" / "__init__.py",
                    APP_DATABASE_INIT_CONTENT_FOR_SQL,
                )

                command = "alembic init -t async migrations"

                python_file = get_python_file()

                full_command = f"{python_file} {command}"

                run_subprocess(self.location, full_command)

                write_file(
                    self.location / "migrations" / "env.py", MIGRATIONS_ENV_FILE_CONTENT
                )
            case "nosql":
                pass
            case _:
                raise RuntimeError("Invalid Database Type Selected")
