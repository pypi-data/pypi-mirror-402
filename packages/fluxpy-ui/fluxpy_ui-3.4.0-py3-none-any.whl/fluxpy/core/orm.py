import sqlite3
import os

class Model:
    def __init__(self, **kwargs):
        self._table = self.__class__.__name__.lower()
        self._db = "flux_database.db"
        for key, value in kwargs.items():
            setattr(self, key, value)
        self._create_table(kwargs)

    def _create_table(self, data):
        conn = sqlite3.connect(self._db)
        cursor = conn.cursor()
        columns = ", ".join([f"{k} TEXT" for k in data.keys()])
        cursor.execute(f"CREATE TABLE IF NOT EXISTS {self._table} (id INTEGER PRIMARY KEY AUTOINCREMENT, {columns})")
        conn.commit()
        conn.close()

    def save(self):
        conn = sqlite3.connect(self._db)
        cursor = conn.cursor()
        data = {k: v for k, v in self.__dict__.items() if not k.startswith('_')}
        keys = ", ".join(data.keys())
        placeholders = ", ".join(["?" for _ in data])
        cursor.execute(f"INSERT INTO {self._table} ({keys}) VALUES ({placeholders})", list(data.values()))
        conn.commit()
        conn.close()

    @classmethod
    def all(cls):
        table = cls.__name__.lower()
        db = "flux_database.db"
        if not os.path.exists(db): return []
        conn = sqlite3.connect(db)
        cursor = conn.cursor()
        try:
            cursor.execute(f"SELECT * FROM {table}")
            rows = cursor.fetchall()
            return rows
        except:
            return []
        finally:
            conn.close()
