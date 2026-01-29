from abc import ABC, abstractmethod
from enum import Enum

from tinydb import TinyDB, Query

from edi_core.utils.file import get_path_from_app_dir, ensure_parent_dir_exists


class CreateStrategy(Enum):
    RECREATE = 1
    REUSE_IF_PRESENT = 2


class SimpleKV(ABC):
    @abstractmethod
    def get_str(self, key: str):
        raise NotImplementedError("get_str is not implemented")

    @abstractmethod
    def set_str(self, key: str, value: str):
        raise NotImplementedError("set_str is not implemented")

    @abstractmethod
    def print_all(self):
        raise NotImplementedError("print_all is not implemented")


class TinyDbSimpleKV(SimpleKV):
    db_path: str
    db: TinyDB

    def __init__(self, db_name: str, create_strategy: CreateStrategy = CreateStrategy.RECREATE):
        self.db_path = get_path_from_app_dir(db_name)
        ensure_parent_dir_exists(self.db_path)
        self.db = TinyDB(f'{self.db_path}.json')
        if create_strategy == CreateStrategy.RECREATE:
            self.db.truncate()

    def get_str(self, key: str):
        results = self.db.search(Query().key == key)
        if len(results) == 0:
            raise KeyError("Key not found")
        return results[0]["value"]

    def set_str(self, key: str, value: str):
        self.db.remove(Query().key == key)
        self.db.insert({"key": key, "value": value})

    def print_all(self):
        return self.db.all()
