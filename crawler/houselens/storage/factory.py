from typing import Dict, Type
import logging
import os
import importlib
import pkgutil
from .base import IDataStorage
from ..config import AppConfig

class StorageFactory:
    """
    Factory and Registry for Storage implementations.
    """
    _registry: Dict[str, Type[IDataStorage]] = {}
    _instance = None

    @classmethod
    def register(cls, storage_type: str):
        """Decorator to register a storage class"""
        def wrapper(storage_cls: Type[IDataStorage]):
            cls._registry[storage_type] = storage_cls
            return storage_cls
        return wrapper

    @classmethod
    def get_storage(cls) -> IDataStorage:
        """
        Returns a cached instance of the Storage based on environment configuration.
        """
        if cls._instance is not None:
            return cls._instance
            
        storage_type = AppConfig.STORAGE_TYPE
        if storage_type not in cls._registry:
            raise ValueError(f"Storage implementation for '{storage_type}' is not registered.")
        
        storage_cls = cls._registry[storage_type]
        logging.info(f"Instantiating storage: {storage_type}")
        cls._instance = storage_cls()
        return cls._instance

# Auto-discover and import all modules in the storage package at load time
# This ensures decorators are triggered without placing imports inside functions
for _, module_name, _ in pkgutil.iter_modules([os.path.dirname(__file__)]):
    if module_name != "base" and module_name != "factory":
        importlib.import_module(f"{__package__}.{module_name}")
