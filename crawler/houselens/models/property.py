from pydantic import BaseModel, Field, model_validator
from typing import Optional, List
from enum import Enum

class BuildingType(str, Enum):
    BUILDING = "大樓"
    MANSION = "華廈"
    APARTMENT = "公寓"
    HOUSE = "透天"
    LAND = "土地"
    PARKING = "車位"
    OTHER = "其他"

class StandardProperty(BaseModel):
    """
    Standardized property model for all crawling sources.
    Every spider must convert its raw data into this model.
    """
    # ====== 核心必備欄位 (Global & Identifiers) ======
    property_uuid: str = Field(..., description="Global Unique Identifier")
    source_platform: str = Field(..., description="來源平台 (e.g., 591, 永慶)")
    source_id: str = Field(..., description="平台原始物件 ID")
    
    # ====== 核心必備欄位 (Basic Info) ======
    title: str = Field(..., description="標題")
    total_price: float = Field(..., description="總價 (萬)")
    unit_price: float = Field(..., description="單價 (萬/坪)")
    
    # 建築特徵
    building_ping: float = Field(..., description="建坪 (總權狀坪數)")
    building_type: BuildingType = Field(default=BuildingType.OTHER, description="建物型態 (標準化分類)")
    raw_building_type: Optional[str] = Field(default=None, description="平台原始提供的建物型態字串")
    
    # 格局數量拆分
    rooms: Optional[int] = Field(default=0, description="房間數量")
    living_rooms: Optional[int] = Field(default=0, description="客/大廳數量")
    bathrooms: Optional[int] = Field(default=0, description="衛浴數量")
    kitchens: Optional[int] = Field(default=0, description="廚房數量")
    balconies: Optional[int] = Field(default=0, description="陽台數量")
    age: float = Field(..., description="屋齡 (年)")
    floor: str = Field(..., description="樓層 (e.g., 5F, B1)")
    total_floor: str = Field(..., description="總樓層 (e.g., 15F)")
    
    # 位置與連結
    address: str = Field(..., description="地址")
    url: str = Field(..., description="物件網址")

    # ====== 面積明細 (Area Details) ======
    main_building_ping: Optional[float] = Field(default=None, description="主建物坪數")
    accessory_ping: Optional[float] = Field(default=None, description="附屬建物坪數 (陽台/雨遮等)")
    shared_ping: Optional[float] = Field(default=None, description="共有部分坪數 (公設)")
    land_ping: Optional[float] = Field(default=None, description="土地坪數")
    indoor_ping: Optional[float] = Field(default=None, description="室內坪數 (主建物 + 附屬建物)")

    # ====== 車位細節 (Parking Details) ======
    has_parking: Optional[bool] = Field(default=None, description="是否有車位")
    parking_type: Optional[str] = Field(default=None, description="車位型態 (坡道平面, 機械等)")
    parking_ping: Optional[float] = Field(default=None, description="車位坪數")

    # ====== 產權與法規細節 (Legal & Ownership) ======
    legal_usage: Optional[str] = Field(default=None, description="法定/謄本用途 (e.g., 住家用, 集合住宅)")
    has_tenant: Optional[bool] = Field(default=None, description="是否有帶租約 (買賣不破租賃)")
    land_zoning: Optional[str] = Field(default=None, description="土地使用分區")

    # ====== 選擇性輔助欄位 (Optional & Extra Info) ======
    community_name: Optional[str] = None        # 社區名稱
    builder: Optional[str] = None               # 建商
    
    management_fee: Optional[str] = Field(default=None, description="管理費 (含單位，e.g. 3600元/月)")
    orientation: Optional[str] = None           # 座向/朝向
    latitude: Optional[float] = None            # 緯度
    longitude: Optional[float] = None           # 經度
    image_urls: List[str] = Field(default_factory=list, description="物件圖片網址列表")

    @model_validator(mode='after')
    def standardize_building_type(self) -> 'StandardProperty':
        """
        根據平台原始提供的資訊 (raw_building_type, total_floor, floor 等)
        動態分類建物型態，修正平台可能標錯的資料。
        """
        raw_type = self.raw_building_type or ""
        total_floor_num = 0
        
        # 嘗試從 total_floor 取出數字 (e.g., "15F" -> 15, "15" -> 15)
        if self.total_floor:
            import re
            match = re.search(r'\d+', self.total_floor)
            if match:
                total_floor_num = int(match.group())

        # 簡單解析當前樓層範圍 (用於判斷透天)
        floor_start = 999
        floor_end = 0
        if self.floor:
            import re
            nums = re.findall(r'\d+', self.floor)
            if nums:
                nums = [int(n) for n in nums]
                floor_start = min(nums)
                floor_end = max(nums)

        # 土地與車位
        if "土地" in raw_type:
            self.building_type = BuildingType.LAND
            return self
        if "車位" in raw_type:
            self.building_type = BuildingType.PARKING
            return self

        # 大樓: 型態包含「大樓」，或樓高大於 10 樓。
        if "大樓" in raw_type or total_floor_num > 10:
            self.building_type = BuildingType.BUILDING
            return self

        # 華廈: 型態包含「華」，或樓高大於等於 5 樓，且樓高小於等於 10 樓。
        if "華" in raw_type or (5 <= total_floor_num <= 10):
            self.building_type = BuildingType.MANSION
            return self

        # 透天: 型態包含「透」，或樓高小於等於 5 樓，且樓層(起)小於等於 1 樓，且樓層(迄)等於樓高。
        is_tou_tian_floors = (total_floor_num > 0 and total_floor_num <= 5) and (floor_start <= 1) and (floor_end == total_floor_num)
        if "透" in raw_type or is_tou_tian_floors:
            self.building_type = BuildingType.HOUSE
            return self

        # 公寓: 型態包含「公」，或樓高小於等於 5 樓，且無電梯或無提供電梯資訊。
        # (這裡假設無電梯由外部決定，但如果前面都沒命中，且樓高 <= 5，很大機率是公寓)
        if "公" in raw_type or (total_floor_num > 0 and total_floor_num <= 5):
            self.building_type = BuildingType.APARTMENT
            return self

        return self
