from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseTransformer(ABC):
    """
    純抽象介面：所有的 Transformer (Property, Community 等) 都必須實作此介面。
    統一接收 raw_data 並返回對應的 Model。
    """
    @abstractmethod
    def transform(self, raw_data: Dict[str, Any]) -> Any:
        pass
