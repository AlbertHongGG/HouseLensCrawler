import re
from typing import Dict, Any, Optional
from ...models.property import StandardProperty
from ..base_components import BaseParser

class SinyiParser(BaseParser):
    """
    Parses located elements from Sinyi pages into standard PropertyInfo objects.
    """
    def extract_source_id(self, url: str) -> str:
        match = re.search(r'/house/([A-Z0-9a-z]+)', url)
        return match.group(1) if match else ""

    def parse(self, elements: Dict[str, Any], url: str, source_id: str) -> Optional[StandardProperty]:
        if 'title' not in elements or 'price' not in elements:
            return None
            
        title = self.clean_text(elements.get('title'))
        # 移除標題結尾可能的雜訊
        if '｜' in title:
            title = title.split('｜')[0].strip()
            
        total_price = self.extract_float(self.clean_text(elements.get('price')))
        
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
        accessory_ping = 0.0
        shared_ping = 0.0
        unit_price = 0.0
        land_ping = 0.0
        balcony_ping = 0.0
        rain_cover_ping = 0.0
        age = 0.0
        floor = ""
        total_floors = ""
        layout = ""
        building_type = ""
        parking_type = ""
        management_fee = ""
        orientation = ""
        has_parking = False
        
        # 處理基本資料區塊
        basic_block = elements.get('_basic_block')
        if basic_block:
            lines = basic_block.text.split('\n')
            lines = [l.strip() for l in lines if l.strip()]
            
            for i, line in enumerate(lines):
                next_line = lines[i+1] if i + 1 < len(lines) else ""
                
                if "建坪" == line and "單價" not in line:
                    if "坪" in next_line:
                        building_ping = self.extract_float(next_line)
                elif line == "建坪單價":
                    if "萬/坪" in next_line:
                        unit_price = self.extract_float(next_line)
                elif line in ["主建物", "主+附"]:
                    if "坪" in next_line:
                        main_building_ping = self.extract_float(next_line)
                elif line == "共有部份":
                    if "坪" in next_line:
                        shared_ping = self.extract_float(next_line)
                elif line == "附屬建物":
                    if "坪" in next_line:
                        accessory_ping = self.extract_float(next_line)
                elif line == "地坪":
                    if "坪" in next_line:
                        land_ping = self.extract_float(next_line)
                elif line == "陽台":
                    if "坪" in next_line:
                        balcony_ping = self.extract_float(next_line)
                elif line == "雨遮":
                    if "坪" in next_line:
                        rain_cover_ping = self.extract_float(next_line)
                elif line == "類型":
                    if next_line and next_line != "--":
                        building_type = next_line
                elif line == "格局":
                    if "房" in next_line or "廳" in next_line:
                        layout = next_line
                elif line == "屋齡":
                    if "預售" in next_line:
                        age = 0.0
                    else:
                        age = self.parse_age(next_line)
                elif line == "樓層":
                    if "/" in next_line:
                        f, tf = self.parse_floor(next_line)
                        floor = f.replace('樓', '').replace('B', '-').strip()
                        total_floors = tf.replace('樓', '').strip()
                elif line == "車位":
                    if next_line != "--" and next_line != "無" and next_line:
                        has_parking = True
                        pt = next_line.replace('收合', '').replace('更多', '').strip()
                        nn_line = lines[i+2] if i + 2 < len(lines) else ""
                        if '萬)' in nn_line or nn_line.endswith(')'):
                            pt += nn_line.replace('收合', '').replace('更多', '').strip()
                        parking_type = pt
                elif line == "警衛管理":
                    if next_line and next_line != "--":
                        management_fee = next_line
                elif line == "建物朝向" or line == "落地窗朝向":
                    if next_line and next_line != "--":
                        orientation = next_line

        layout_data = self.parse_layout(layout)

        if not unit_price:
            unit_price = round(total_price / building_ping, 2) if building_ping else 0.0

        if not accessory_ping and (balcony_ping > 0 or rain_cover_ping > 0):
            accessory_ping = round(balcony_ping + rain_cover_ping, 2)

        indoor_ping = None
        if main_building_ping and accessory_ping:
            indoor_ping = round(main_building_ping + accessory_ping, 2)

        return StandardProperty(
            property_uuid=f"sinyi_{source_id}",
            source_platform="sinyi",
            source_id=source_id,
            url=url,
            title=title,
            address=address,
            total_price=total_price,
            unit_price=unit_price,
            building_ping=building_ping,
            main_building_ping=main_building_ping,
            accessory_ping=accessory_ping or None,
            shared_ping=shared_ping or None,
            land_ping=land_ping or None,
            indoor_ping=indoor_ping,
            raw_building_type=building_type or None,
            age=age,
            floor=str(floor) if floor else "",
            total_floor=str(total_floors) if total_floors else "",
            rooms=layout_data.get('rooms'),
            living_rooms=layout_data.get('living_rooms'),
            bathrooms=layout_data.get('bathrooms'),
            management_fee=management_fee or None,
            orientation=orientation or None,
            parking_type=parking_type or None,
            has_parking=has_parking
        )
