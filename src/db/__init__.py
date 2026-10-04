"""Storage backends. get_database() picks one from the environment:

- DATABASE_URL=mysql://user:pass@host:port/db  -> MySQL (src/db/mysql_store.py, schema in sql/mysql-schema.sql)
- otherwise                                    -> MongoDB via MONGODB_URI / MONGODB_DB (default)
"""
import os


def get_database():
    url = (os.getenv("DATABASE_URL") or "").strip().strip("\"'")
    if url.startswith("mysql"):
        from .mysql_store import MySQLDatabase
        return MySQLDatabase(url)
    from .mongo import AgriDatabase
    return AgriDatabase()


def __getattr__(name):  # lazy: a MySQL run never opens a Mongo client
    if name == "AgriDatabase":
        from .mongo import AgriDatabase
        return AgriDatabase
    if name == "MySQLDatabase":
        from .mysql_store import MySQLDatabase
        return MySQLDatabase
    raise AttributeError(name)


__all__ = ["get_database", "AgriDatabase", "MySQLDatabase"]
