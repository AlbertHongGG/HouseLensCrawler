import json
import logging
import sys
from houselens.engine.context import SpiderContext, EngineContext
from houselens.engine.events import Event
from houselens.spider.factory import SpiderFactory

from DrissionPage import ChromiumPage, ChromiumOptions

logging.basicConfig(level=logging.INFO)

def main():
    try:
        with open('data/golden_dataset.json', 'r', encoding='utf-8') as f:
            golden_data = json.load(f)
    except Exception as e:
        print(f'Failed to load golden dataset: {e}')
        sys.exit(1)

    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--site', type=str, default='all')
    args = parser.parse_args()

    TARGETS = [
        ('591', 'https://sale.591.com.tw/home/house/detail/2/20258064.html'),
        ('yungching', 'https://buy.yungching.com.tw/house/6861494'),
        ('sinyi', 'https://www.sinyi.com.tw/buy/house/8014GX')
    ]
    if args.site != 'all':
        TARGETS = [t for t in TARGETS if t[0] == args.site]

    new_data = {}

    from houselens.engine.events import event_bus

    def on_item_parsed(item):
        new_data[f"{item.source_platform}_{item.source_id}"] = item.dict()

    event_bus.subscribe(Event.ITEM_PARSED, on_item_parsed)

    opts = ChromiumOptions()
    opts.headless(True)
    browser = ChromiumPage(opts)

    engine_ctx = EngineContext()
    context = SpiderContext(engine_context=engine_ctx, max_items=10)

    try:
        for platform_name, url in TARGETS:
            print(f"Testing {platform_name} with URL {url}")
            spider = SpiderFactory.create(platform_name)
            # Since process_detail_url already emits EVENT, we don't need to manually do it
            spider.process_detail_url(url, browser, context)
    finally:
        browser.quit()

    has_error = False
    for key, expected_item in golden_data.items():
        if key not in new_data:
            print(f'[FAIL] {key} was not extracted in the new run!')
            has_error = True
            continue
            
        actual_item = new_data[key]
        
        if '591' in key:
            if 'property_uuid' in expected_item:
                del expected_item['property_uuid']
            if 'property_uuid' in actual_item:
                del actual_item['property_uuid']
            if 'image_urls' in expected_item and 'image_urls' in actual_item:
                expected_item['image_urls'] = len(expected_item['image_urls'])
                actual_item['image_urls'] = len(actual_item['image_urls'])

        # Compare all fields
        for field, expected_val in expected_item.items():
            actual_val = actual_item.get(field)
            if actual_val != expected_val:
                msg = f'[FAIL] {key} - Field "{field}" mismatch! Expected: {repr(expected_val)}, Got: {repr(actual_val)}'
                try:
                    print(msg)
                except UnicodeEncodeError:
                    sys.stdout.buffer.write((msg + '\n').encode('utf-8', 'replace'))
                has_error = True

    if has_error:
        print('\n[FAIL] Golden Dataset Verification FAILED. Regressions detected!')
        sys.exit(1)
    else:
        print('\n✅ Golden Dataset Verification PASSED. Zero regressions detected!')
        sys.exit(0)

if __name__ == "__main__":
    main()
