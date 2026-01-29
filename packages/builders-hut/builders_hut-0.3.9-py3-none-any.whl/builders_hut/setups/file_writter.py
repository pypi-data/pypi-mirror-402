from builders_hut.setups import FILES_TO_WRITE, BaseSetup
from builders_hut.utils import write_file


class SetupFileWriter(BaseSetup):
    """
    Write data to the files created previously
    """

    def create(self):
        self._write_files()

    def _write_files(self) -> None:
        for path, content in FILES_TO_WRITE.items():
            if path.name == ".env":
                content = content.format(
                    title=self.name,
                    description=self.description,
                    version=self.version,
                )
            path = self.location / path
            write_file(path, content)

    def configure(self, name: str, description: str, version: str):
        self.name = name
        self.description = description
        self.version = version
