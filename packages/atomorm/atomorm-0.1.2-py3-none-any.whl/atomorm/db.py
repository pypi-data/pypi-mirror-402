import sqlite3
from pathlib import Path


class Engine:
    def __init__(self, db_url):
        path = Path(db_url.replace("sqlite:///", ""))
        self.path = Path(path).expanduser().resolve()

    def connect(self):
        return sqlite3.connect(self.path)


class Session:
    def __init__(self, engine):
        self.engine = engine
        self.conn = engine.connect()

    def execute(self, sql, params=None):
        if params is None:
            params = []
        return self.conn.execute(sql, params)

    def commit(self):
        self.conn.commit()

    def close(self):
        self.conn.close()

    def get(self, cls, value):
        if value is None:
            raise ValueError(f"cannot find with None value")
        tablename = cls._meta["table_name"]
        fields = cls._meta["fields"]
        pk_field = cls._meta["primary_key"]
        pk_name = pk_field.column_name
        sql = f"SELECT * FROM {tablename} WHERE {pk_name} = {value}"
        cursor = self.execute(sql)
        row = cursor.fetchone()
        data = {name: row[idx] for idx, name in enumerate(fields.keys())}
        return cls(**data)
