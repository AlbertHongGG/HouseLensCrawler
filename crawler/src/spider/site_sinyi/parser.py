import re
from typing import Dict, Any, Optional
from ...models.property import StandardProperty

class SinyiParser:
    """
    Parses located elements from Sinyi pages into standard PropertyInfo objects.
    """
    
    def _clean_text(self, ele) -> str:
        if not ele:
            return ""
        return re.sub(r'[\r\n\t\s]+', ' ', ele.text).strip()

    def _extract_number(self, text: str) -> float:
        if not text:
            return 0.0
        # 移除非數字與小數點的字元
        cleaned = re.sub(r'[^\d.]', '', text)
        if not cleaned:
            return 0.0
        try:
            return float(cleaned)
        except ValueError:
            return 0.0

    def parse(self, elements: Dict[str, Any], url: str, source_id: str) -> Optional[StandardProperty]:
        if 'title' not in elements or 'price' not in elements:
            return None
            
        title = self._clean_text(elements.get('title'))
        # 移除標題結尾可能的雜訊
        if '｜' in title:
            title = title.split('｜')[0].strip()
            
        price_text = self._clean_text(elements.get('price'))
        total_price = self._extract_number(price_text)
        
        # Address
        address = ""
        addr_text = elements.get('address')
        if addr_text:
            lines = addr_text.text.split('\n')
            for line in lines:
                if '地址' in line:
                    # 處理如 "地址台北市內湖區安泰街建坪單價69.94 萬/坪" 這種黏在一起的字串
                    addr = line.replace('地址', '')
                    if '建坪' in addr:
                        addr = addr.split('建坪')[0]
                    address = addr.strip()
                    break
            
        # 預設值
        building_ping = 0.0
        main_building_ping = 0.0
        age = 0.0
        floor = ""
        total_floors = ""
        layout = ""
        parking_type = ""
        management_fee = ""
        orientation = ""
        has_parking = False
        
        # 處理基本資料區塊
        basic_block = elements.get('basic_block')
        if basic_block:
            # 取得所有文字並以換行分割
            lines = basic_block.text.split('\n')
            lines = [l.strip() for l in lines if l.strip()]
            
            for i, line in enumerate(lines):
                next_line = lines[i+1] if i + 1 < len(lines) else ""
                
                if "建坪" == line and "單價" not in line:
                    # 避免抓到 "建坪單價"
                    if "坪" in next_line:
                        building_ping = self._extract_number(next_line)
                elif line in ["主建物", "主+附"]:
                    if "坪" in next_line:
                        main_building_ping = self._extract_number(next_line)
                elif line == "格局":
                    if "房" in next_line or "廳" in next_line:
                        layout = next_line
                elif line == "屋齡":
                    if "預售" in next_line:
                        age = 0.0
                    else:
                        age = self._extract_number(next_line)
                elif line == "樓層":
                    if "/" in next_line:
                        parts = next_line.split('/')
                        floor = parts[0].replace('樓', '').replace('B', '-').strip()
                        total_floors = parts[1].replace('樓', '').strip()
                elif line == "車位":
                    if next_line != "--" and next_line != "無" and next_line:
                        has_parking = True
                        parking_type = next_line
                elif line == "警衛管理":
                    if next_line and next_line != "--":
                        management_fee = next_line
                elif line == "建物朝向" or line == "落地窗朝向":
                    if next_line and next_line != "--":
                        orientation = next_line

        rooms, living_rooms, bathrooms = None, None, None
        if layout:
            r_match = re.search(r'(\d+)房', layout)
            if r_match: rooms = int(r_match.group(1))
            l_match = re.search(r'(\d+)廳', layout)
            if l_match: living_rooms = int(l_match.group(1))
            b_match = re.search(r'(\d+)衛', layout)
            if b_match: bathrooms = int(b_match.group(1))

        return StandardProperty(
            property_uuid=f"sinyi_{source_id}",
            source_platform="sinyi",
            source_id=source_id,
            url=url,
            title=title,
            address=address,
            total_price=total_price,
            unit_price=round(total_price / building_ping, 2) if building_ping else 0.0,
            building_ping=building_ping,
            main_building_ping=main_building_ping,
            age=age,
            floor=str(floor) if floor else "",
            total_floor=str(total_floors) if total_floors else "",
            rooms=rooms,
            living_rooms=living_rooms,
            bathrooms=bathrooms,
            management_fee=management_fee or None,
            orientation=orientation or None,
            raw_parking_type=parking_type or None,
            has_parking=has_parking
        )
