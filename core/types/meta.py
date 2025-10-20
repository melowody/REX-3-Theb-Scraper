"""
Defines the Singleton metaclasses for use in classes that should only be instantiated once
"""

from abc import ABCMeta
from typing import Any


class SingletonMeta(type):
    """This is an implementation of the Singleton
        object type as a metaclass.

        When this metaclass is used, it creates a Singleton."""
    _instances: dict[type, Any] = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(SingletonMeta, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class SingletonABCMeta(ABCMeta):
    """This is an implementation of ABC (Abstract Base Class)
        metaclass that is also a singleton.

        When this metaclass is used, it creates an abstract class
        that becomes a singleton when used as a parent class.

        This has to be separate from SingletonMeta as it has a different parent class."""
    _instances: dict[type, Any] = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(SingletonABCMeta, cls).__call__(*args, **kwargs)
        return cls._instances[cls]
