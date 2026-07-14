from pydantic import BaseModel, Field
from datetime import datetime

class DuplicateRecord(BaseModel):
    platform: str = Field(..., description="平台名稱")
    source_id: str = Field(..., description="原始 ID")
    url_a: str = Field(..., description="首次抓取的網址")
    url_b: str = Field(..., description="本次重複抓取的網址")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat(), description="發生時間")
