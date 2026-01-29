from pathlib import Path
from typing import TypeVar

class Record:
    def __init__(self, id: int, path: Path):
        self.id = id
        self.path = path

RecordType = TypeVar('RecordType', bound=Record)