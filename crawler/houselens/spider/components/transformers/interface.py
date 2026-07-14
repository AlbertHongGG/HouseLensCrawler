from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from ....models.property import StandardProperty

class ITransformer(ABC):
    """
    Transformer 負責將 RuleEngine 提取的原始資料 (Raw Data Dict)，
    進一步清理並轉換為領域物件 (StandardProperty)。
    """
    @abstractmethod
    def extract_source_id(self, url: str) -> Optional[str]:
        """從網址萃取來源 ID (source_id)"""
        pass

    @abstractmethod
    def transform(self, raw_data: Dict[str, Any], url: str, source_id: str) -> Optional[StandardProperty]:
        """將原始資料轉換為 StandardProperty 物件"""
        pass
