from typing import List

from tinydb import TinyDB
from tinydb.table import Document


class Tiny:
    _db = None

    def __init__(self, db_file):
        self._db = TinyDB(db_file)

    def insert(self, data: dict) -> int:
        return self._db.insert(data)

    def all(self) -> List[Document]:
        return self._db.all()

    def search(self, query) -> List[Document]:
        return self._db.search(query)

    def close(self):
        self._db.close()
