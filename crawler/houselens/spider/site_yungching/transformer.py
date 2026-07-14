import re
from typing import Optional, Dict, Any
from ..components.transformers.interface import ITransformer
from ...models.property import StandardProperty
from ...utils.parsers import parse_layout, parse_floor

class SpiderYungchingTransformer(ITransformer):
    def extract_source_id(self, url: str) -> str:
        return url.split('/')[-1].split('?')[0]

    def transform(self, raw_data: Dict[str, Any], url: str, source_id: str) -> Optional[StandardProperty]:
        title = raw_data.get('title') or f"永慶房屋 - {source_id}"
        total_price = float(raw_data.get('total_price') or 0.0)
        
        # Unit price priority
        unit_price = float(raw_data.get('unit_price') or 0.0)
        if not unit_price:
            unit_price = float(raw_data.get('unit_price_fallback') or 0.0)
            
        address_raw = str(raw_data.get('address') or "").strip()
        address = address_raw.split('\n')[0].strip() if '\n' in address_raw else address_raw

        layout_text = str(raw_data.get('layout') or "")
        layout_data = parse_layout(layout_text)

        building_ping = float(raw_data.get('building_ping') or 0.0)
        main_ping = float(raw_data.get('main_building_ping') or 0.0)
        shared_ping = float(raw_data.get('shared_ping') or 0.0)
        accessory_ping = float(raw_data.get('accessory_ping') or 0.0)
        land_ping = float(raw_data.get('land_ping') or 0.0)

        # Fallback unit price
        if unit_price == 0.0 and total_price > 0 and building_ping > 0:
            unit_price = round(total_price / building_ping, 2)

        age = float(raw_data.get('age') or 0.0)
        floor, total_floor = parse_floor(str(raw_data.get('floor_info') or ""))

        raw_building_type = str(raw_data.get('raw_building_type') or "")
        if not raw_building_type:
            # Fallback to extract from layout string
            if "型態" in layout_text:
                raw_building_type = layout_text.split("型態")[-1].strip()

        legal_usage = str(raw_data.get('legal_usage') or "")
        land_zoning = str(raw_data.get('land_zoning') or "")

        community_name = str(raw_data.get('community_name') or "")
        if "看更多" in community_name:
            community_name = community_name.split("看更多")[0].strip()

        # Parking
        has_parking = False
        hp_text = str(raw_data.get('has_parking') or "")
        if hp_text:
            if "無車位" not in hp_text and "0個車位" not in hp_text and "0.0個車位" not in hp_text:
                has_parking = True

        parking_type = ""
        parking_text = str(raw_data.get('parking_type') or "")
        if parking_text:
            parking_type = parking_text.strip()

        management_fee = str(raw_data.get('management_fee') or "")
        if "管理費" in management_fee:
            management_fee = management_fee.split("管理費")[-1].strip()
        elif "建物管理費" in management_fee:
            management_fee = management_fee.split("建物管理費")[-1].strip()

        orientation = str(raw_data.get('orientation') or "")

        prop = StandardProperty(
            property_uuid=f"yc_{source_id}",
            source_platform="yungching",
            source_id=source_id,
            title=title,
            total_price=total_price,
            unit_price=unit_price,
            builder=None,
            management_fee=management_fee or None,
            orientation=orientation or None,
            latitude=None,
            building_ping=building_ping,
            main_building_ping=main_ping,
            shared_ping=shared_ping,
            accessory_ping=accessory_ping,
            land_ping=land_ping,
            indoor_ping=round(main_ping + accessory_ping, 2) if main_ping else None,
            rooms=layout_data.get('rooms'),
            living_rooms=layout_data.get('living_rooms'),
            bathrooms=layout_data.get('bathrooms'),
            age=age,
            floor=floor,
            total_floor=total_floor,
            address=address,
            url=url,
            raw_building_type=raw_building_type or None,
            legal_usage=legal_usage or None,
            land_zoning=land_zoning or None,
            has_tenant=None,
            has_parking=has_parking,
            parking_type=parking_type or None,
            parking_ping=None,
            community_name=community_name or None,
            image_urls=[src for src in (raw_data.get('image_urls') or []) if src and "base64" not in src and "blank" not in src]
        )
        return prop
