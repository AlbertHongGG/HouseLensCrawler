import logging
from typing import List, Optional, Any, Dict, Callable, Tuple, Union
from DrissionPage.items import ChromiumElement
from .selectors import BaseSelector
from .processors import BaseProcessor

class FieldRule:
    """
    Defines how to extract and process a single field from the DOM.
    """
    def __init__(
        self,
        name: str,
        selector: BaseSelector,
        processors: Optional[List[BaseProcessor]] = None,
        default: Any = None,
        extract_attr: str = 'text',
        is_list: bool = False
    ):
        self.name = name
        self.selector = selector
        self.processors = processors or []
        self.default = default
        self.extract_attr = extract_attr
        self.is_list = is_list

    def extract(self, context: ChromiumElement) -> Tuple[Any, Optional[Union[ChromiumElement, List[ChromiumElement]]]]:
        """
        Executes the rule against the context.
        Returns a tuple: (processed_value, source_element(s))
        """
        try:
            if self.is_list:
                elements = self.selector.select_all(context)
                if not elements:
                    return self.default, []
                
                raw_values = []
                for ele in elements:
                    val = ele.attr(self.extract_attr) if self.extract_attr != 'text' else ele.text
                    raw_values.append(val)
                
                # Apply processors to each item
                processed_values = []
                for val in raw_values:
                    current_val = val
                    for processor in self.processors:
                        current_val = processor.process(current_val)
                    processed_values.append(current_val)
                return processed_values, elements
            else:
                element = self.selector.select(context)
                if not element:
                    return self.default, None
                    
                raw_value = element.attr(self.extract_attr) if self.extract_attr != 'text' else element.text
                
                # Apply processors
                current_val = raw_value
                for processor in self.processors:
                    current_val = processor.process(current_val)
                return current_val, element
                
        except Exception as e:
            logging.debug(f"Failed to extract field '{self.name}': {e}")
            return self.default, None


class BlockRule:
    """
    Defines a reusable block of fields that share a common container.
    """
    def __init__(self, name: str, container_selector: BaseSelector, fields: List[FieldRule]):
        self.name = name
        self.container_selector = container_selector
        self.fields = fields
        
    def extract(self, page_context: ChromiumElement) -> Dict[str, Any]:
        container = self.container_selector.select(page_context)
        if not container:
            return {}
            
        result = {}
        for field in self.fields:
            val, _ = field.extract(container)
            result[field.name] = val
        return result


import re

class KeyValueRule:
    """
    Finds a list of container elements, extracts key and value from each,
    cleans the key (stripping HTML), and maps them to standard field names.
    This bypasses anti-scraping tag obfuscation (e.g. 591's <vsm> tags).
    """
    def __init__(
        self,
        container_selector: BaseSelector,
        key_selector: BaseSelector,
        value_selector: BaseSelector,
        key_mapping: Dict[str, str],
        value_processors: Optional[Dict[str, List[BaseProcessor]]] = None
    ):
        self.container_selector = container_selector
        self.key_selector = key_selector
        self.value_selector = value_selector
        self.key_mapping = key_mapping
        self.value_processors = value_processors or {}

    def _clean_key(self, html: str) -> str:
        # Strip all HTML tags
        text = re.sub(r'<[^>]+>', '', html)
        # Remove spaces, newlines, and fullwidth colons
        text = text.replace(' ', '').replace('\n', '').strip()
        text = text.split('：')[0].split(':')[0]
        return text

    def _clean_value(self, html: str) -> str:
        # Strip all HTML tags but don't split by colon
        text = re.sub(r'<[^>]+>', '', html)
        # We can keep spaces if needed, but usually these are small attributes
        text = text.replace(' ', '').replace('\n', '').strip()
        return text

    def extract(self, context: ChromiumElement) -> Tuple[Dict[str, Any], Dict[str, ChromiumElement]]:
        results = {}
        elements = {}
        container_eles = self.container_selector.select_all(context)
        
        if not container_eles:
            print(f"[DEBUG] KeyValueRule container_selector {self.container_selector} NOT FOUND")
            return results, elements
            
        for container in container_eles:
            key_ele = self.key_selector.select(container)
            value_ele = self.value_selector.select(container)
            
            if key_ele and value_ele:
                clean_key = self._clean_key(key_ele.html)
                print(f"[DEBUG] KeyValueRule clean_key: '{clean_key}'")
                
                # Check if this cleaned key exists in our mapping
                for mapped_key_name, target_field in self.key_mapping.items():
                    if mapped_key_name in clean_key:
                        raw_value = self._clean_value(value_ele.html)
                        
                        # Apply processors if any
                        processors = self.value_processors.get(target_field, [])
                        current_val = raw_value
                        for processor in processors:
                            current_val = processor.process(current_val)
                            
                        results[target_field] = current_val
                        elements[target_field] = value_ele
                        break
                        
        return results, elements


class MappingProfile:
    """
    A collection of rules that define how to scrape a specific page type.
    """
    def __init__(
        self,
        rules: List[FieldRule],
        blocks: Optional[List[BlockRule]] = None,
        key_value_rules: Optional[List[KeyValueRule]] = None
    ):
        self.rules = rules
        self.blocks = blocks or []
        self.key_value_rules = key_value_rules or []


class RuleEngine:
    """
    Executes a MappingProfile against a ChromiumPage.
    Also handles emitting events for the Visualizer automatically!
    """
    def __init__(self, event_bus_emitter: Optional[Callable] = None):
        self.emit_event = event_bus_emitter

    def execute(self, profile: MappingProfile, tab: ChromiumElement, source_id: str, platform_name: str) -> Dict[str, Any]:
        result = {}
        elements_map = {} # For visualizer
        
        # 1. Execute top-level rules
        for rule in profile.rules:
            val, ele = rule.extract(tab)
            result[rule.name] = val
            if ele:
                elements_map[rule.name] = ele
                
        # 2. Execute block rules
        for block in profile.blocks:
            container = block.container_selector.select(tab)
            if container:
                print(f"[DEBUG] Block '{block.name}' container FOUND!")
                for field in block.fields:
                    val, ele = field.extract(container)
                    result[field.name] = val
                    if ele:
                        elements_map[field.name] = ele
            else:
                print(f"[DEBUG] Block '{block.name}' container NOT FOUND!")
                        
        # 3. Execute Key-Value mapping rules (Anti-obfuscation)
        for kv_rule in profile.key_value_rules:
            kv_results, kv_elements = kv_rule.extract(tab)
            result.update(kv_results)
            elements_map.update(kv_elements)
                        
        # 4. Emit event for Visualizer if an emitter is provided
        if self.emit_event and elements_map:
            self.emit_event(
                tab=tab,
                elements=elements_map,
                source_id=source_id,
                platform_name=platform_name
            )
            
        return result
