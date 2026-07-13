import asyncio
from src.spider.site_591.locator import Spider591Locator
from src.spider.site_591.parser import Spider591Parser
from DrissionPage import ChromiumPage

def main():
    p = ChromiumPage()
    url = "https://sale.591.com.tw/home/house/detail/2/20496562.html"
    p.get(url)
    import time
    time.sleep(1.5)
    
    locator = Spider591Locator()
    parser = Spider591Parser()
    
    print("Locating elements...")
    house_boxes = p.eles('.detail-house-box')
    with open('boxes_debug.html', 'w', encoding='utf-8') as f:
        for i, box in enumerate(house_boxes):
            f.write(f"<!-- BOX {i} -->\n")
            f.write(box.html + "\n\n")
    elements = locator.locate(p)
    if 'raw_building_type' in elements and elements['raw_building_type']:
        print("RAW BUILDING TYPE ELE TEXT:", repr(elements['raw_building_type'].text))
    else:
        print("House data box missing or raw_building_type empty!")
    print("Parsing elements...")
    prop = parser.parse(elements, url, "20496562")
    
    print("\n--- Parsed Property ---")
    import json
    with open("test_output.json", "w", encoding="utf-8") as f:
        f.write(json.dumps(prop.model_dump(), indent=2, ensure_ascii=False))
    print("Saved to test_output.json")
    
    p.quit()
    
if __name__ == "__main__":
    main()
