import logging
from .interfaces import IStorage
from ..config import AppConfig

class StorageProvider:
    """
    Dependency Injection container for Storage.
    Provides the correct storage implementation based on AppConfig.STORAGE_TYPE.
    """
    _storage = None

    @classmethod
    def get_storage(cls) -> IStorage:
        if cls._storage is None:
            if AppConfig.STORAGE_TYPE == "supabase":
                from .supabase import SupabaseStorage
                logging.info("[Provider] Instantiating Supabase Storage")
                cls._storage = SupabaseStorage()
            else:
                from .json import JsonStorage
                logging.info("[Provider] Instantiating JSON Storage")
                cls._storage = JsonStorage()
        return cls._storage
