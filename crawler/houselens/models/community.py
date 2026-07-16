from pydantic import BaseModel, Field
from typing import Optional

class StandardCommunity(BaseModel):
    """
    Standardized community model for all crawling sources.
    """
    community_uuid: str = Field(..., description="Global Unique Identifier (e.g. sinyi_0009465)")
    source_platform: str = Field(..., description="來源平台 (e.g., 591, yungching, sinyi)")
    source_id: str = Field(..., description="平台原始社區 ID")
    url: str = Field(..., description="社區網址")

    # 基本資料
    name: str = Field(..., description="社區名稱")
    address: Optional[str] = Field(default=None, description="社區地址")
    
    # 詳細規格
    builder: Optional[str] = Field(default=None, description="建設公司 (建商)")
    contractor: Optional[str] = Field(default=None, description="營造公司")
    completion_date: Optional[str] = Field(default=None, description="完工日期/建築完成日")
    age: Optional[str] = Field(default=None, description="屋齡")
    total_households: Optional[int] = Field(default=None, description="總戶數")
    building_structure: Optional[str] = Field(default=None, description="建築結構 (e.g. RC, SRC)")
    land_zoning: Optional[str] = Field(default=None, description="土地使用分區")
    image_url: Optional[str] = Field(default=None, description="封面圖片網址")
    
    # Supabase mapping uses builder_id which is handled by a trigger, so we don't necessarily need it here,
    # but we will save 'builder' directly, and the DB trigger handles builder table insertion and mapping.
