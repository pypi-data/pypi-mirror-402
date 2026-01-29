from builders_hut.setups import BaseSetup
from typing import Literal
from builders_hut.setups.database import DatabaseFactory


class SetupDatabase(BaseSetup):
    """setup database"""

    def create(self):
        DatabaseFactory(self.database_provider, self.location).setup_db()

    def configure(
        self,
        database_type: Literal["sql", "nosql"],
    ):
        self.database_type = database_type
