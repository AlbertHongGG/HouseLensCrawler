from typing import Dict, Type
import logging
import os
import importlib
import pkgutil
from .base import BaseSpider
from ..config import SpiderConfig

class SpiderFactory:
    """
    Factory and Registry for Spider implementations.
    """
    _registry: Dict[str, Type[BaseSpider]] = {}

    @classmethod
    def register(cls, platform_name: str):
        def wrapper(spider_cls: Type[BaseSpider]):
            cls._registry[platform_name] = spider_cls
            return spider_cls
        return wrapper

    @classmethod
    def create(cls, platform_name: str, **kwargs) -> BaseSpider:
        """
        Creates a Spider instance, injecting its specific environment config.
        """
        if platform_name not in cls._registry:
            raise ValueError(f"Spider implementation for '{platform_name}' is not registered.")
        
        spider_cls = cls._registry[platform_name]
        
        # Build spider-specific configuration dynamically
        config = SpiderConfig(platform_name)
        
        # Instantiate Visualizer if enabled
        from ..config import AppConfig
        visualizer = None
        if AppConfig.ENABLE_VISUAL_VERIFICATION:
            from ..engine.visualizer import VisualVerificationService
            visualizer = VisualVerificationService(output_dir="data")
            logging.info(f"Visual Verification is ENABLED for {platform_name}")
        
        logging.info(f"Instantiating spider: {platform_name} (Max Items: {config.max_items})")
        return spider_cls(config=config, visualizer=visualizer, **kwargs)

# Auto-discover and import all modules in the spider package at load time
# This ensures decorators are triggered without placing imports inside functions
for _, module_name, _ in pkgutil.iter_modules([os.path.dirname(__file__)]):
    if module_name != "base" and module_name != "factory":
        importlib.import_module(f"{__package__}.{module_name}")
