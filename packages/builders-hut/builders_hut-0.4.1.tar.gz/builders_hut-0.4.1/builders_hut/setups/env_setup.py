from builders_hut.setups import BaseSetup
from builders_hut.utils import write_file, run_subprocess, get_python_file
from typing import Literal

PACKAGES = [
    "fastapi",
    "python-dotenv",
    "email-validator",
    "tzdata",
    "pydantic-settings",
    "scalar-fastapi",
    "uvicorn",
    "jinja2",
]

DEV_PACKAGES = ["pytest"]


DB_SQL_PACKAGES = {
    "postgres": ["sqlmodel", "asyncpg", "psycopg2-binary"],
    "mysql": ["sqlmodel", "aiomysql", "pymysql"],
    "sqlite": ["sqlmodel", "aiosqlite"],
}

SQL_COMMON_PACKAGE = ["alembic"]

DEV_PACKAGES_EXTENDED = ["-r requirements.txt"]


class SetupEnv(BaseSetup):
    """Create Env and Install Base Packages"""

    def create(self):
        try:
            try:
                if self.database_type == "sql":
                    PACKAGES.extend(SQL_COMMON_PACKAGE)
                    PACKAGES.extend(DB_SQL_PACKAGES[self.database_provider])

                write_file(self.location / "requirements.txt", "\n".join(PACKAGES))

                DEV_PACKAGES_EXTENDED.extend(DEV_PACKAGES)
                write_file(
                    self.location / "requirements_dev.txt",
                    "\n".join(DEV_PACKAGES_EXTENDED),
                )

            except Exception as e:
                print(e)
                raise RuntimeError("Could not write to requirements file")

            try:
                run_subprocess(self.location, "python -m venv .venv")

            except Exception:
                raise RuntimeError("Could not create virtual env for project")

            command = "pip install -r requirements_dev.txt"
            python_file = get_python_file()

            full_command = f"{python_file} {command}"

            try:
                run_subprocess(self.location, full_command)
            except Exception:
                raise RuntimeError("Could not install packages")

        except Exception as e:
            raise RuntimeError(f"Failed to create environment: {str(e)}")

    def configure(
        self,
        name: str,
        description: str,
        version: str,
        database_provider: Literal["postgres", "mysql", "sqlite", "mongodb"],
        database_type: Literal["sql", "nosql"],
        **kwargs,
    ):
        self.name = name
        self.description = description
        self.version = version
        self.database_provider = database_provider
        self.database_type = database_type
