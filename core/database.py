"""
Outlines the database connection class RExDBPool
"""

from contextlib import contextmanager
import os
from typing import Generator
from psycopg2 import pool, extensions
from core.types.meta import SingletonABCMeta


class RExDBPool(metaclass=SingletonABCMeta):
    """
    The main DB Pool for connecting to the REx PostgresQL Database
    """

    _pool: pool.SimpleConnectionPool | None = None

    def __init__(self):
        if self._pool is None:
            self._pool = pool.SimpleConnectionPool(
                1,
                10,
                database=os.getenv("POSTGRESQL_DB"),
                user=os.getenv("POSTGRESQL_USER"),
                password=os.getenv("POSTGRESQL_PASS"),
                host=os.getenv("POSTGRESQL_HOST"),
                port=os.getenv("POSTGRESQL_PORT")
            )

    @contextmanager
    def get_conn(self, autocommit: bool = False) -> Generator[extensions.connection, None, None]:
        """
        Yields a connection from the pool, automatically returning it when done.

        Args:
            autocommit (bool, optional): Whether to commit after every execute,
            or after all the executes. Defaults to False.

        Yields:
            psycopg2.extensions.connection: A connection from the pool.
        """

        if self._pool is None:
            return
        conn = self._pool.getconn()
        try:
            if autocommit:
                conn.autocommit = True
            yield conn
            if not autocommit:
                conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            self._pool.putconn(conn)

    @contextmanager
    def get_cursor(self, autocommit: bool = False) -> Generator[extensions.cursor, None, None]:
        """
        Yields the cursor for a connection from the pool, automatically returning it when done.

        Args:
            autocommit (bool, optional): Whether to commit after every execute,
            or after all the executes. Defaults to False.

        Yields:
            psycopg2.extensions.cursor: The cursor for a connection from the pool.
        """
        with self.get_conn(autocommit=autocommit) as conn:
            with conn.cursor() as cursor:
                yield cursor

    def close_all(self):
        """
        Closes all connections
        """
        if self._pool is None:
            return
        self._pool.closeall()
