from tinydb import TinyDB, Query
from pathlib import Path
from typing import Any

class Storage:
    def __init__(self, storage_dir: str = "/worker/storage"):
        self._path = Path(storage_dir).expanduser()
        self._path.mkdir(parents=True, exist_ok=True)

        self.rules = TinyDB(self._path / "rules.json")
        self.hashes = TinyDB(self._path / "hashes.json")
        self.hashqueue = TinyDB(self._path / "hashqueue.json")
        self.bases = TinyDB(self._path / "bases.json")
        self.result = TinyDB(self._path / "result.json")

    def insert(self, db: str, data: dict) -> int:
        return self._get_db(db).insert(data)

    def find(self, db: str, **kwargs) -> list[dict]:
        q = Query()
        expr = None
        for k, v in kwargs.items():
            condition = (q[k] == v)
            expr = condition if expr is None else expr & condition
        return self._get_db(db).search(expr)

    def update(self, db: str, data: dict, **where) -> int:
        q = Query()
        expr = None
        for k, v in where.items():
            condition = (q[k] == v)
            expr = condition if expr is None else expr & condition
        return self._get_db(db).update(data, expr)

    def delete(self, db: str, **where) -> int:
        q = Query()
        expr = None
        for k, v in where.items():
            condition = (q[k] == v)
            expr = condition if expr is None else expr & condition
        return self._get_db(db).remove(expr)

    def all(self, db: str) -> list[dict]:
        return self._get_db(db).all()
    
    def delall(self, db: str):
        return self._get_db(db).truncate()

    def _get_db(self, name: str) -> TinyDB:
        return {
            "rules": self.rules,
            "hashes": self.hashes,
            "hashqueue": self.hashqueue,
            "bases": self.bases,
            "result": self.result
        }[name]
