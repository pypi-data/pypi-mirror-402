from builders_hut.setups import BaseSetup
from builders_hut.utils import get_platform, make_file, write_file, run_subprocess
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


class SetupEnv(BaseSetup):
    """Create Env and Install Base Packages"""

    def create(self):
        try:
            platform = get_platform()

            try:
                if self.database_type == "sql":
                    PACKAGES.extend(SQL_COMMON_PACKAGE)
                    PACKAGES.extend(DB_SQL_PACKAGES[self.database_provider])

                make_file(self.location / "requirements.txt")
                write_file(self.location / "requirements.txt", PACKAGES)

                make_file(self.location / "requirements_dev.txt")
                dev = ["-r requirements.txt"].extend(DEV_PACKAGES)
                write_file(self.location / "requirements_dev.txt", dev)

            except Exception:
                raise RuntimeError("Could not write to requirements file")

            try:
                run_subprocess(self.location, "python -m venv .venv")

            except Exception:
                raise RuntimeError("Could not create virtual env for project")

            command = "pip install -r requirements.txt"
            python_file = (
                ".venv/bin/python -m"
                if platform == "linux"
                else ".venv\\Scripts\\python.exe -m"
            )

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
    ):
        self.name = name
        self.description = description
        self.version = version
        self.database_provider = database_provider
        self.database_type = database_type
