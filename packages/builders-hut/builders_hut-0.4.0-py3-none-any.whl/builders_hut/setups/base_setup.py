from abc import ABC, abstractmethod
from pathlib import Path


class BaseSetup(ABC):
    def __init__(self, location):
        self.location = Path(location) if not isinstance(location, Path) else location

    @abstractmethod
    def create(self):
        """Create the necessary items."""
        pass

    def configure(self, **kwargs):
        """Optional hook"""
        pass
