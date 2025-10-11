from abc import abstractmethod, ABC
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Generic, TypeVar, Type

from core.types.meta import SingletonABCMeta
from core.database import RExDBPool

from psycopg2 import sql

T = TypeVar("T")


@dataclass
class ToLower:
    value: Any


@dataclass
class NotInIndex:
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
    EQUAL = '=',
    LESS_THAN = '<',
    GREATER_THAN = '>',
    LESS_THAN_OR_EQ = '<=',
    GREATER_THAN_OR_EQ = '>=',
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


def query(table_name: str, key_order: tuple[str, ...], selectors: list[Selector], limit: int = 0) -> list[tuple[Any, ...]]:
    """
    Sends a query to the database and returns the result.

    Args:
        table_name (str): The name of the table to query.
        key_order (tuple[str, ...]): The list of keys to get back from the database.
        selectors (list[Selector]): The list of restraints for the query.
        limit (int, optional): The maximum amount of results to get back. Defaults to 0 (infinite).

    Returns:
        list[tuple[Any, ...]]: The list of all the results.
    """
    with RExDBPool().get_cursor() as cursor:
        where_clauses = []
        values = []

        for selector in selectors:
            where_clauses.append(
                sql.SQL("{} {} %s").format(sql.Identifier(selector.key.lower()), sql.SQL(str(selector.comparator))))
            values.append(selector.value)

        query_sql = sql.SQL("SELECT {keys} FROM {tbl}").format(
            keys=sql.SQL(", ").join(map(sql.Identifier, [i.lower() for i in key_order])),
            tbl=sql.Identifier(table_name.lower())
        )
        if where_clauses:
            query_sql += sql.SQL(" WHERE ") + sql.SQL(" AND ").join(where_clauses)

        if limit > 0:
            query_sql += sql.SQL(" LIMIT %s")
            values.append(limit)

        cursor.execute(query_sql, values)
        return cursor.fetchall()


def upsert(items: list[T], table_name: str, primary_key: str, get_data: Callable[[T], dict[str, Any]], ignore_conflict: bool = False, is_unique_index: bool = False) -> None:
    """
    Insert items into a table, overriding the other data, or ignoring on conflict.

    Args:
        items (list[T]): The items to insert.
        table_name (str): The name of the table.
        primary_key (str): The primary key of the table.
        get_data (Callable[[T], dict[str, Any]]): The function to get key -> value from an item.
        ignore_conflict (bool, optional): Whether to ignore conflicts. Defaults to False.
        is_unique_index (bool, optional): Whether the primary key is actually a unique index. Defaults to False.
    """

    with RExDBPool().get_cursor() as cursor:
        for i in items:
            data = get_data(i)

            cols = list([i.lower() for i in data.keys()])
            vals = list(map(lower, data.values()))

            insert = sql.SQL("INSERT INTO {table} ({cols}) VALUES ({vals})").format(
                table=sql.Identifier(table_name.lower()),
                cols=sql.SQL(", ").join(map(sql.Identifier, cols)),
                vals=sql.SQL(", ").join(sql.Placeholder() * len(vals))
            )

            if ignore_conflict or len(cols) == 1:
                conflict = sql.SQL("ON CONFLICT ({pk}) DO NOTHING").format(
                    pk=sql.Identifier(primary_key.lower())
                )
            else:
                update_cols = [col for col in cols if col != primary_key.lower()]
                update = sql.SQL(", ").join(
                    sql.Composed([
                        sql.Identifier(col),
                        sql.SQL(" = EXCLUDED."),
                        sql.Identifier(col)
                    ]) for col in update_cols
                )
                start = sql.SQL("ON CONFLICT")
                if is_unique_index:
                    middle = sql.SQL("ON CONSTRAINT {pk}").format(pk=sql.Identifier(primary_key.lower()))
                else:
                    middle = sql.SQL("({pk})").format(pk=sql.Identifier(primary_key.lower()))
                end = sql.SQL("DO UPDATE SET {update}").format(update=update)
                conflict = sql.SQL(" ").join([start, middle, end])

            query_stmt = sql.SQL(" ").join([insert, conflict])

            cursor.execute(query_stmt, vals)


class RExBaseManager(Generic[T], ABC, metaclass=SingletonABCMeta):
    """
    A base manager class for storing and retrieving objects.

    Takes a Generic type to type check the objects against.
    """

    def get_t(self) -> Type[T]:
        for cls in self.__class__.__mro__:
            if hasattr(cls, "__parameters__") and cls.__parameters__:
                return cls.__parameters__[0]
        raise TypeError("Could not get type T")

    def __init__(self) -> None:
        self._objects: list[T] = []
        self.read_from_db()

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

    @abstractmethod
    def read_from_db(self) -> None:
        """
        Reads all objects from the DB into the RExManager's object list.
        """
        pass

    @abstractmethod
    def write_to_db(self) -> None:
        """
        Writes all objects from the RExManager's object list to the DB.
        """
        pass

    def get_one(self, predicate: Callable[[T], bool], not_found: Any) -> T | NotInIndex:
        if len(search := self.get(predicate)) > 0:
            return search[0]
        return NotInIndex(not_found, self.get_t())


class RExManager(RExBaseManager[T], ABC, metaclass=SingletonABCMeta):

    @property
    @abstractmethod
    def table_name(self) -> str:
        pass

    @property
    @abstractmethod
    def key_order(self) -> tuple[str, ...]:
        pass

    @property
    @abstractmethod
    def primary_key(self) -> str:
        pass

    @property
    def is_unique_index(self) -> bool:
        return False

    @abstractmethod
    def parse_db_result(self, result: tuple[Any, ...]) -> T:
        pass

    @abstractmethod
    def prepare_db_entry(self, item: T) -> dict[str, Any]:
        pass

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
        upsert(self.get_all(), self.table_name, self.primary_key, self.prepare_db_entry, ignore_conflict)