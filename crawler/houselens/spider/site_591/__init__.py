"""
591 Spider Module.
This module exposes the Spider591 class and automatically registers it with the SpiderFactory.
"""
from .spider import Spider591
from ..factory import SpiderFactory

# 將 Spider591 註冊至工廠
SpiderFactory.register("591")(Spider591)
