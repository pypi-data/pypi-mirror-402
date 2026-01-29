from pathlib import Path

from builders_hut.setups import FILES_TO_WRITE, BaseSetup


class SetupFileWriter(BaseSetup):
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
            self._write_file(path, content)

    @staticmethod
    def _write_file(path: Path, content: str) -> None:
        if not path.exists():
            raise FileNotFoundError(f"{path} does not exist")

        path.write_text(content, encoding="utf-8")

    def configure(self, name: str, description: str, version: str):
        self.name = name
        self.description = description
        self.version = version
