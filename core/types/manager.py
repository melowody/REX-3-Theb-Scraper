"""
Outlines all the functions and classes required for the class managers.
These allow for easy storage to and retrieval from large lists of data.
"""

from collections.abc import Hashable
import functools
from abc import abstractmethod, ABC
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Generic, TypeVar, Type
from psycopg2 import sql

from core.types.meta import SingletonABCMeta
from core.database import RExDBPool

T = TypeVar("T")
U = TypeVar("U", bound=Hashable)


@dataclass
class ToLower:
    """
    Ensures that this gets lowercased before interacting with the DB
    """
    value: Any


@dataclass
class NotInIndex:
    """
    This is returned from managers if the specified item isn't found
    """
    value: Any
    type: Type

    def __str__(self):
        return f"({self.value} NOT IN {self.type.__name__}'S INDEX)"


def lower(value: str | ToLower) -> str:
    """
    Convert to lowercase any values that request to be.

    Args:
        value (Any): The value to lowercase.

    Returns:
        Any: The value lowercased.
    """
    if not isinstance(value, ToLower):
        return value
    return value.value.lower()


class Comparator(Enum):
    """
    An enum of the comparison operators in postgresql, to ensure a valid comparison
    """
    EQUAL = '='
    LESS_THAN = '<'
    GREATER_THAN = '>'
    LESS_THAN_OR_EQ = '<='
    GREATER_THAN_OR_EQ = '>='
    NOT_EQUAL = '!='

    def __str__(self) -> str:
        return str(self.value)


@dataclass
class Selector:
    """A class storing a singular query data"""
    key: str
    """The key of the query"""
    value: Any
    """The value of the query"""
    comparator: Comparator
    """The comparator in the query"""


class DBHolder(Generic[T], ABC):
    """
    DB Table Information Holder
    """
    @property
    @abstractmethod
    def table_name(self) -> str:
        """
        The name of the associated DB table
        """

    @property
    @abstractmethod
    def key_order(self) -> tuple[str, ...]:
        """
        The order of the keys to ensure parse_db_result handles them correctly.
        """

    @property
    @abstractmethod
    def primary_key(self) -> str:
        """
        The primary key/constraint in the DB.
        """

    @property
    def is_unique_index(self) -> bool:
        """
        Whether or not the primary key is a unique index or a normal key.
        """
        return False

    @abstractmethod
    def parse_db_result(self, result: tuple[Any, ...]) -> T:
        """
        Parses a single DB SELECT result into the Manager's object.
        
        Args:
            result (tuple[Any, ...]): The result from the DB in the specified key order.
        
        Returns:
            T: The parsed object.
        """

    @abstractmethod
    def prepare_db_entry(self, item: T) -> dict[str, Any]:
        """
        Prepares a single item to be uploaded to the DB.
        
        Args:
            item (T): The item to be prepared.
        
        Returns:
            dict[str, Any]: The key-value pairs to be sent to the DB.
        """

    @abstractmethod
    def get_delete_keys(self, item: T) -> dict[str, Any]:
        """
        Get the key-value pairs to ensure the correct item gets deleted.
        
        Args:
            item (T): The item to get the key-value pairs from.
        
        Returns:
            dict[str, Any]: The key-value pairs.
        """

def query(table_name: str,
          key_order: tuple[str, ...],
          selectors: list[Selector | sql.SQL],
          limit: int | None = None) -> \
        list[tuple[Any, ...]]:
    """
    Sends a query to the database and returns the result.

    Args:
        table_name (str): The name of the table to query.
        key_order (tuple[str, ...]): The list of keys to get back from the database.
        selectors (list[Selector | sql.SQL]): The list of restraints for the query.
        limit (int, optional): The maximum amount of results to get back. Defaults to 0 (infinite).

    Returns:
        list[tuple[Any, ...]]: The list of all the results.
    """
    with RExDBPool().get_cursor() as cursor:
        where_clauses = []
        values = []

        # Format and append all the WHERE clauses to the query
        for selector in selectors:
            if isinstance(selector, Selector):
                clause: sql.SQL | sql.Composed = sql.SQL("{} {} %s") \
                    .format(sql.Identifier(selector.key.lower()),
                    sql.SQL(selector.comparator.value))
                values.append(selector.value)
            else:
                clause = selector
            where_clauses.append(clause)

        # Format the whole query clause, including the SELECT statement
        query_sql = sql.SQL("SELECT {keys} FROM {tbl} tbl").format(
            keys=sql.SQL(", ").join(map(sql.SQL, [f"tbl.{i.lower()}" for i in key_order])),
            tbl=sql.Identifier(table_name.lower())
        )

        # Add the WHERE clauses
        if where_clauses:
            query_sql += sql.SQL(" WHERE ") + sql.SQL(" AND ").join(where_clauses)

        # Add the LIMIT clause
        if limit:
            query_sql += sql.SQL(" LIMIT %s")
            values.append(limit)

        cursor.execute(query_sql, values)
        return cursor.fetchall()


def delete(table_name: str, *selectors: Selector | sql.SQL):
    """
    Deletes an item from the DB.

    Args:
        table_name (str): The name of the table to query.
        selectors (list[Selector | sql.SQL]): The list of restraints for the query.
    """
    with RExDBPool().get_cursor() as cursor:
        where_clauses = []
        values = []

        # Format the selectors
        for selector in selectors:
            if isinstance(selector, Selector):
                clause: sql.SQL | sql.Composed = sql.SQL("{} {} %s") \
                    .format(sql.Identifier(selector.key.lower()),
                    sql.SQL(selector.comparator.value))
                values.append(selector.value)
            else:
                clause = selector
            where_clauses.append(clause)

        # Format the whole statement and add the WHERE clauses
        query_sql = sql.SQL("DELETE FROM {tbl} tbl").format(
            tbl=sql.Identifier(table_name.lower())
        )
        if where_clauses:
            query_sql += sql.SQL(" WHERE ") + sql.SQL(" AND ").join(where_clauses)

        cursor.execute(query_sql, values)


def upsert(items: list[T], manager: DBHolder[T], ignore_conflict: bool = False) -> None:
    """
    Insert items into a table, overriding the other data, or ignoring on conflict.

    Args:
        items (list[T]): The items to insert.
        ignore_conflict (bool, optional): Whether to ignore conflicts. Defaults to False.
    """

    with RExDBPool().get_cursor() as cursor:
        for i in items:
            data = manager.prepare_db_entry(i)

            # Split the list into keys and values
            cols = [i.lower() for i in data.keys()]
            vals = list(map(lower, data.values()))

            # Format the sql statement
            insert = sql.SQL("INSERT INTO {table} ({cols}) VALUES ({vals})").format(
                table=sql.Identifier(manager.table_name.lower()),
                cols=sql.SQL(", ").join(map(sql.Identifier, cols)),
                vals=sql.SQL(", ").join(sql.Placeholder() * len(vals))
            )

            # Add the ON CONFLICT section to deal with conflicts
            if ignore_conflict or len(cols) == 1:
                conflict = sql.SQL("ON CONFLICT ({pk}) DO NOTHING").format(
                    pk=sql.Identifier(manager.primary_key.lower())
                )
            else:
                update_cols = [col for col in cols if col != manager.primary_key.lower()]
                update = sql.SQL(", ").join(
                    sql.Composed([
                        sql.Identifier(col),
                        sql.SQL(" = EXCLUDED."),
                        sql.Identifier(col)
                    ]) for col in update_cols
                )
                conflict_parts: list[sql.SQL | sql.Composed] = [sql.SQL("ON CONFLICT")]
                if manager.is_unique_index:
                    conflict_parts.append(sql.SQL("ON CONSTRAINT {pk}").format(
                        pk=sql.Identifier(manager.primary_key.lower())))
                else:
                    conflict_parts.append(sql.SQL("({pk})").format(
                        pk=sql.Identifier(manager.primary_key.lower())))
                conflict_parts.append(sql.SQL("DO UPDATE SET {update}").format(update=update))
                conflict = sql.SQL(" ").join(conflict_parts)

            # Join and execute
            query_stmt = sql.SQL(" ").join([insert, conflict])

            try:
                cursor.execute(query_stmt, vals)
            except Exception as e: # pylint: disable=broad-except
                print(e)


class RExBaseManager(Generic[T, U], ABC, metaclass=SingletonABCMeta):
    """
    A base manager class for storing and retrieving objects.

    Takes a Generic type to type check the objects against.
    """

    def __init__(self) -> None:
        self._objects: list[T] = []
        self.read_from_db()

    def clear_caches(self):
        """
        Clear all the function caches
        """
        self.get_by.cache_clear()

    @functools.lru_cache
    def get_by(self, value: U) -> T | NotInIndex:
        """
        Get an item by its ID
        
        Args:
            value (U): The ID to get the item by
            
        Returns:
            T | NotInIndex: The item, or a NotInIndex if it doesn't exist.
        """
        return self._get_by_impl(value)

    @abstractmethod
    def _get_by_impl(self, value: U) -> T | NotInIndex:
        pass

    def get_all(self) -> list[T]:
        """
        Gets a shallow copy of the RExManager's object list.

        Returns:
            list[T]: A shallow copy of the object list.
        """
        return self._objects[:]

    def exists(self, predicate: Callable[[T], bool]) -> bool:
        """
        Checks whether any object exists in the RExManager's
        object list that satisfies the predicate function.

        Args:
            predicate (Callable[[T], bool]): The function to check each object against.

        Returns:
            bool: Whether the object exists in the RExManager's object list.
        """
        return any(map(predicate, self.get_all()))

    def add(self, obj: T) -> None:
        """
        Adds an object to the RExManager's object list if it doesn't exist.

        Checking uses the __eq__ function in the T class.

        Args:
            obj (T): The object to add.
        """
        if not self.exists(lambda x: obj == x):
            self._objects.append(obj)
        self.clear_caches()

    def get(self, predicate: Callable[[T], bool]) -> list[T]:
        """
        Gets a list of all objects in the RExManager's object
        list that satisfy the predicate function.

        Args:
            predicate (Callable[[T], bool]): The function to check each object against.

        Returns:
            list[T]: A list of all objects that satisfy the predicate function.
        """
        return [obj for obj in self.get_all() if predicate(obj)]

    def delete(self, predicate: Callable[[T], bool]) -> None:
        """
        Deletes all objects in the RExManager's object list
        that satisfy the predicate function.

        Args:
            predicate (Callable[[T], bool]): The function to check each object against
        """
        for obj in self.get(predicate):
            self._objects.remove(obj)
            self.remove_from_db(obj)
        self.clear_caches()

    def ensure(self, predicate: Callable[[T], bool], factory: Callable[[], T]) -> list[T]:
        """
        Gets a list of all objects in the RExManager's object
        list that satisfy the predicate function, or creates an object
        if none exist.

        Args:
            predicate (Callable[[T], bool]): The function to check each object against
            factory (Callable[[], T]): The function used to create a new object

        Returns:
            list[T]: A list of all objects that satisfy the predicate function
        """
        if len(items := self.get(predicate)) > 0:
            return items
        out = factory()
        self.add(out)
        self.clear_caches()
        return [out]

    def upsert(self, obj: T) -> None:
        """
        Adds an object to the RExManager's object list, replacing
        the old object if it exists.

        This uses the __eq__ function to check if the object exists.

        Args:
            obj (T): The object to add
        """
        self.delete(lambda x: x == obj)
        self.add(obj)
        self.clear_caches()

    @abstractmethod
    def read_from_db(self) -> None:
        """
        Reads all objects from the DB into the RExManager's object list.
        """

    @abstractmethod
    def write_to_db(self) -> None:
        """
        Writes all objects from the RExManager's object list to the DB.
        """

    @abstractmethod
    def remove_from_db(self, item: T) -> None:
        """
        Remove a specific item from the DB
        
        Args:
            item (T): The item to remove from the DB.
        """

    def get_one(self, predicate: Callable[[T], bool], not_found: Any) -> T | NotInIndex:
        """
        Gets one item based on the given predicate, otherwise returns a NotInIndex.
        
        Args:
            predicate (Callable[[T], bool]): The predicate to compare each item to.
            not_found (Any): The message to return in the NotInIndex.
        
        Returns:
            T | NotInIndex: The found item, otherwise NotInIndex.
        """
        if len(search := self.get(predicate)) > 0:
            return search[0]
        return NotInIndex(not_found, type(self))


class RExManager(RExBaseManager[T, U], DBHolder, ABC, metaclass=SingletonABCMeta):
    """
    An implementation of RExBaseManager with database support.
    """

    def __init__(self):
        super().__init__()
        if self not in MANAGERS:
            MANAGERS.append(self)

    def read_from_db(self) -> None:
        """
        Reads all objects from the DB into the RExManager's object list.
        """
        for i in query(self.table_name, self.key_order, []):
            self.add(self.parse_db_result(i))

    def write_to_db(self, ignore_conflict: bool = False) -> None:
        """
        Writes all the items in the RExManager's object list into the DB.

        Params:
            ignore_conflict (bool, optional): Whether to ignore conflict in the DB
        """
        upsert(self.get_all(), self, ignore_conflict)

    def remove_from_db(self, item: T) -> None:
        selectors = []
        for k, v in self.get_delete_keys(item).items():
            selectors.append(Selector(k, v, Comparator.EQUAL))
        delete(self.table_name, *selectors)


MANAGERS: list[RExManager] = []
