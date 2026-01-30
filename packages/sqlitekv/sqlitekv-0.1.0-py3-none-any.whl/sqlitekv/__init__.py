import sqlite3
import pickle
from typing import Any
from pathlib import Path


class Cache():
    def __init__(self, cache_name="cache", cache_path='~/sqlitekv_db'):
        self.connection = sqlite3.connect(Path(cache_path).expanduser().absolute())
        self.cache_uri = cache_name
        self.connection.execute(
            f"CREATE TABLE IF NOT EXISTS {self.cache_uri} (key text unique, value text)",
        )

    def exists(self, key: str) -> bool:
        return self.connection.execute(
            f"SELECT EXISTS(SELECT 1 FROM {self.cache_uri} WHERE key = ?)",
            [key],
        ).fetchone()[0]

    def get(self, key: str) -> Any:
        try:
            result = self.connection.execute(
                f"SELECT value FROM {self.cache_uri} WHERE key = ?",
                [key],
            ).fetchone()[0]
            return pickle.loads(result)
        except Exception as e:
            print(e)

    def put(self, key: str, object: Any):
        try:
            value = pickle.dumps(object)
            self.connection.execute(
                f"INSERT INTO {self.cache_uri} VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value=?",  # noqa: E501
                [key, value, value],
            )
            self.connection.commit()
        except Exception as e:
            print(e)