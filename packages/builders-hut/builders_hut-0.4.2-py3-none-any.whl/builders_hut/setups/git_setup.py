from builders_hut.setups import BaseSetup
from builders_hut.utils import run_subprocess


class SetupGithub(BaseSetup):
    """
    Setup github for this project
    """

    def create(self):
        try:
            run_subprocess(self.location, "git init")
        except Exception:
            raise RuntimeError("Could Not Initialize Git")
