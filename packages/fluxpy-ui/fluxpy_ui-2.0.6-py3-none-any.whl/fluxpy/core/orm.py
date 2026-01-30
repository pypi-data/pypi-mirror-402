import sqlite3
import os

class Model:
    database = "flux_db.sqlite"
    table_name = ""

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    @classmethod
    def _get_conn(cls):
        return sqlite3.connect(cls.database)

    @classmethod
    def create_table(cls, **fields):
        cls.table_name = cls.__name__.lower()
        columns = ", ".join([f"{name} {type}" for name, type in fields.items()])
        query = f"CREATE TABLE IF NOT EXISTS {cls.table_name} (id INTEGER PRIMARY KEY AUTOINCREMENT, {columns})"
        with cls._get_conn() as conn:
            conn.execute(query)

    def save(self):
        fields = {k: v for k, v in self.__dict__.items() if not k.startswith('_')}
        columns = ", ".join(fields.keys())
        placeholders = ", ".join(["?" for _ in fields])
        query = f"INSERT INTO {self.table_name} ({columns}) VALUES ({placeholders})"
        with self._get_conn() as conn:
            conn.execute(query, list(fields.values()))

    @classmethod
    def all(cls):
        cls.table_name = cls.__name__.lower()
        query = f"SELECT * FROM {cls.table_name}"
        with cls._get_conn() as conn:
            cursor = conn.execute(query)
            rows = cursor.fetchall()
            # Get column names
            cols = [description[0] for description in cursor.description]
            return [cls(**dict(zip(cols, row))) for row in rows]
