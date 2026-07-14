import re
import uuid
from typing import Dict, Any, Optional
from ..components.transformers.interface import ITransformer
from ...models.property import StandardProperty
from ...utils.parsers import parse_layout, parse_floor

class SpiderSinyiTransformer(ITransformer):
    def extract_source_id(self, url: str) -> str:
        match = re.search(r'/house/([A-Z0-9a-z]+)', url)
        return match.group(1) if match else ""

    def transform(self, raw_data: Dict[str, Any], url: str, source_id: str) -> Optional[StandardProperty]:
        title = str(raw_data.get('title') or "")
        if '｜' in title:
            title = title.split('｜')[0].strip()
        if not title:
            title = f"信義房屋 - {source_id}"
            
        total_price = float(raw_data.get('total_price') or 0.0)
        
        # Address cleaning
        address = str(raw_data.get('address') or "").replace('地址', '')
        if '建坪' in address:
            address = address.split('建坪')[0]
        address = address.strip()

        building_ping = float(raw_data.get('building_ping') or 0.0)
        unit_price = float(raw_data.get('unit_price') or 0.0)
        if not unit_price and building_ping > 0 and total_price > 0:
            unit_price = round(total_price / building_ping, 2)

        main_building_ping = float(raw_data.get('main_building_ping') or 0.0)
        shared_ping = float(raw_data.get('shared_ping') or 0.0)
        accessory_ping = float(raw_data.get('accessory_ping') or 0.0)
        land_ping = float(raw_data.get('land_ping') or 0.0)
        
        balcony_ping = float(raw_data.get('balcony_ping') or 0.0)
        rain_cover_ping = float(raw_data.get('rain_cover_ping') or 0.0)
        
        if not accessory_ping and (balcony_ping > 0 or rain_cover_ping > 0):
            accessory_ping = round(balcony_ping + rain_cover_ping, 2)

        indoor_ping = None
        if main_building_ping and accessory_ping:
            indoor_ping = round(main_building_ping + accessory_ping, 2)

        raw_building_type = str(raw_data.get('raw_building_type') or "").replace('--', '').strip()
        
        layout_data = parse_layout(str(raw_data.get('layout') or ""))
        age = float(raw_data.get('age') or 0.0)
        
        floor_text = str(raw_data.get('floor_info') or "")
        f, tf = parse_floor(floor_text)
        floor = f.replace('樓', '').replace('B', '-').strip()
        total_floor = tf.replace('樓', '').strip()

        parking_ping = float(raw_data.get('parking_ping') or 0.0)
        
        parking_type = str(raw_data.get('parking_type') or "").replace('--', '').replace('無', '').strip()
        has_parking = False
        if parking_type:
            has_parking = True
        elif '無' in str(raw_data.get('parking_type') or ""):
            has_parking = False
            
        management_fee = str(raw_data.get('management_fee') or "").replace('--', '').strip()
        orientation = str(raw_data.get('orientation') or "").replace('--', '').strip()

        prop = StandardProperty(
            property_uuid=f"sinyi_{source_id}",
            source_platform="sinyi",
            source_id=source_id,
            url=url,
            title=title,
            address=address,
            total_price=total_price,
            unit_price=unit_price,
            building_ping=building_ping,
            main_building_ping=main_building_ping or None,
            accessory_ping=accessory_ping or None,
            shared_ping=shared_ping or None,
            land_ping=land_ping or None,
            indoor_ping=indoor_ping,
            raw_building_type=raw_building_type or None,
            age=age,
            floor=floor,
            total_floor=total_floor,
            rooms=layout_data.get('rooms'),
            living_rooms=layout_data.get('living_rooms'),
            bathrooms=layout_data.get('bathrooms'),
            management_fee=management_fee or None,
            orientation=orientation or None,
            parking_type=parking_type or None,
            has_parking=has_parking,
            parking_ping=parking_ping or None,
            image_urls=[src if src.startswith("http") else "https:" + src for src in (raw_data.get('image_urls') or []) if src]
        )
        return prop
