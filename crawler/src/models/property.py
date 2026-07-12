from pydantic import BaseModel, Field
from typing import Optional

class StandardProperty(BaseModel):
    """
    Standardized property model for all crawling sources.
    Every spider must convert its raw data into this model.
    """
    # 必要欄位 (必要但不見得抓得到，用 Optional 保留彈性，但我們期待要有)
    property_uuid: str = Field(..., description="Global Unique Identifier")
    source_platform: str = Field(..., description="來源平台 (e.g., 591, 永慶)")
    source_id: str = Field(..., description="平台原始物件 ID")
    
    title: str = Field(..., description="標題")
    total_price: float = Field(..., description="總價 (萬)")
    unit_price: float = Field(..., description="單價 (萬/坪)")
    building_ping: float = Field(..., description="建坪")
    
    layout: str = Field(..., description="格局 (e.g., 3房2廳2衛)")
    age: float = Field(..., description="屋齡")
    floor: str = Field(..., description="樓層 (e.g., 5F)")
    total_floor: str = Field(..., description="總樓層 (e.g., 15F)")
    address: str = Field(..., description="地址")
    url: str = Field(..., description="物件網址")

    # 選擇性欄位
    main_building_ping: Optional[float] = None  # 主建坪
    indoor_ping: Optional[float] = None         # 室內坪
    latitude: Optional[float] = None            # 緯度
    longitude: Optional[float] = None           # 經度
    community_name: Optional[str] = None        # 社區名稱
    project_name: Optional[str] = None          # 建案名稱
    builder: Optional[str] = None               # 建商
    parking: Optional[str] = None               # 車位
    publish_time: Optional[str] = None          # 刊登時間
    update_time: Optional[str] = None           # 更新時間
    
    management_fee: Optional[float] = None      # 管理費
    orientation: Optional[str] = None           # 座向/朝向
    balcony: Optional[str] = None               # 陽台
    decoration: Optional[str] = None            # 裝潢
    land_zoning: Optional[str] = None           # 使用分區
    land_ping: Optional[float] = None           # 土地坪數
