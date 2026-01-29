from typing import Literal
from builders_hut.utils import make_file, write_file
from pathlib import Path
from builders_hut.setups.file_contents import APP_DATABASE_SESSION_CONTENT_FOR_SQL


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
                make_file(self.location / "app" / "database" / "session.py")
                write_file(
                    self.location / "app" / "database" / "session.py",
                    APP_DATABASE_SESSION_CONTENT_FOR_SQL,
                )
            case "nosql":
                pass
            case _:
                raise RuntimeError("Invalid Database Type Selected")
