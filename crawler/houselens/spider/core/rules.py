import logging
import re
from abc import ABC, abstractmethod
from typing import List, Optional, Any, Dict, Callable, Tuple, Union
from DrissionPage.items import ChromiumElement
from .selectors import BaseSelector
from .processors import BaseProcessor
from .post_processors import BasePostProcessor

class BaseRule(ABC):
    """
    Abstract base class for all rules.
    Every rule must implement `extract` which returns a tuple of:
    (Dict of extracted field names and values, Dict of field names and source elements)
    """
    @abstractmethod
    def extract(self, context: ChromiumElement) -> Tuple[Dict[str, Any], Dict[str, ChromiumElement]]:
        pass


class ContainerRule(BaseRule):
    """
    Locates a single structural block (container) in the DOM and executes its child rules inside it.
    This creates a Progressive Localization Tree.
    """
    def __init__(self, name: str, selector: BaseSelector, rules: List[BaseRule]):
        self.name = name
        self.selector = selector
        self.rules = rules
        
    def extract(self, context: ChromiumElement) -> Tuple[Dict[str, Any], Dict[str, ChromiumElement]]:
        container = self.selector.select(context)
        if not container:
            logging.debug(f"[ContainerRule] '{self.name}' NOT FOUND using {self.selector}")
            return {}, {}
            
        logging.debug(f"[ContainerRule] '{self.name}' FOUND")
        results = {}
        elements = {}
        
        for rule in self.rules:
            r_results, r_elements = rule.extract(container)
            results.update(r_results)
            elements.update(r_elements)
            
        return results, elements


class ListRule(BaseRule):
    """
    Locates multiple identical blocks (list items) in the DOM and executes its child rules inside EACH item.
    Useful for extracting lists of specs, rows in a table, or multiple key-value pairs.
    """
    def __init__(self, name: str, item_selector: BaseSelector, rules: List[BaseRule]):
        self.name = name
        self.item_selector = item_selector
        self.rules = rules

    def extract(self, context: ChromiumElement) -> Tuple[Dict[str, Any], Dict[str, ChromiumElement]]:
        results = {}
        elements = {}
        items = self.item_selector.select_all(context)
        
        if not items:
            logging.debug(f"[ListRule] '{self.name}' items NOT FOUND using {self.item_selector}")
            return results, elements
            
        logging.debug(f"[ListRule] '{self.name}' FOUND {len(items)} items")
        
        for item in items:
            for rule in self.rules:
                r_results, r_elements = rule.extract(item)
                results.update(r_results)
                elements.update(r_elements)
                
        return results, elements


class FieldRule(BaseRule):
    """
    Leaf node rule. Defines how to extract and process a single field from the current DOM context.
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

    def extract(self, context: ChromiumElement) -> Tuple[Dict[str, Any], Dict[str, ChromiumElement]]:
        results = {}
        elements = {}
        try:
            if self.is_list:
                eles = self.selector.select_all(context)
                if not eles:
                    return {self.name: self.default}, {}
                
                raw_values = []
                for ele in eles:
                    val = ele.attr(self.extract_attr) if self.extract_attr != 'text' else ele.text
                    raw_values.append(val)
                
                processed_values = []
                for val in raw_values:
                    current_val = val
                    for processor in self.processors:
                        current_val = processor.process(current_val)
                    processed_values.append(current_val)
                    
                results[self.name] = processed_values
                elements[self.name] = eles
            else:
                ele = self.selector.select(context)
                if not ele:
                    return {self.name: self.default}, {}
                    
                raw_value = ele.attr(self.extract_attr) if self.extract_attr != 'text' else ele.text
                
                current_val = raw_value
                for processor in self.processors:
                    current_val = processor.process(current_val)
                
                results[self.name] = current_val
                elements[self.name] = ele
                
        except Exception as e:
            logging.debug(f"Failed to extract field '{self.name}': {e}")
            results[self.name] = self.default
            
        return results, elements


class KeyValueExtractionRule(BaseRule):
    """
    Special rule used inside a ListRule. 
    It extracts a key and a value from the context, checks if the key matches a mapping, 
    and outputs the mapped field name and processed value.
    """
    def __init__(
        self,
        key_selector: BaseSelector,
        value_selector: BaseSelector,
        key_mapping: Dict[str, str],
        value_processors: Optional[Dict[str, List[BaseProcessor]]] = None
    ):
        self.key_selector = key_selector
        self.value_selector = value_selector
        self.key_mapping = key_mapping
        self.value_processors = value_processors or {}

    def _clean_key(self, html: str) -> str:
        text = re.sub(r'<[^>]+>', '', html)
        text = text.replace(' ', '').replace('\n', '').strip()
        text = text.split('：')[0].split(':')[0]
        return text

    def _clean_value(self, html: str) -> str:
        text = re.sub(r'<[^>]+>', '', html)
        text = text.replace(' ', '').replace('\n', '').strip()
        return text

    def extract(self, context: ChromiumElement) -> Tuple[Dict[str, Any], Dict[str, ChromiumElement]]:
        key_ele = self.key_selector.select(context)
        value_ele = self.value_selector.select(context)
        
        if key_ele and value_ele:
            clean_key = self._clean_key(key_ele.html)
            
            for mapped_key_name, target_field in self.key_mapping.items():
                if mapped_key_name in clean_key:
                    raw_value = self._clean_value(value_ele.html)
                    
                    processors = self.value_processors.get(target_field, [])
                    current_val = raw_value
                    for processor in processors:
                        current_val = processor.process(current_val)
                        
                    return {target_field: current_val}, {target_field: value_ele}
                    
        return {}, {}


class BlockKeyValueRule(BaseRule):
    """
    A robust rule that takes an entire semantic block (context), cleans all HTML tags,
    checks if a mapped key exists in the text, and returns the parsed value.
    This entirely ignores CSS classes for 'key' or 'value', making it highly resilient
    to DOM obfuscation. Returns the entire block as the highlight element.
    """
    def __init__(
        self,
        key_mapping: Dict[str, str],
        value_processors: Optional[Dict[str, List[BaseProcessor]]] = None
    ):
        self.key_mapping = key_mapping
        self.value_processors = value_processors or {}

    def extract(self, context: ChromiumElement) -> Tuple[Dict[str, Any], Dict[str, ChromiumElement]]:
        if not context:
            return {}, {}
            
        raw_html = context.html
        if not raw_html:
            return {}, {}
            
        # 1. 暴力拔除所有 HTML tags，並移除所有空白與換行
        text = re.sub(r'<[^>]+>', '', raw_html)
        text = text.replace(' ', '').replace('\n', '').strip()
        
        # 2. 檢查是否有任何 mapped key 存在於字串中
        for mapped_key_name, target_field in self.key_mapping.items():
            if mapped_key_name in text:
                # 若包含該 key，則把 key 以及可能出現的冒號剔除，剩下的大部分就是 value
                # 例如: "格局:2房1廳" -> "2房1廳"
                raw_value = text.replace(mapped_key_name, '')
                raw_value = raw_value.replace(':', '').replace('：', '')
                
                # 3. 處理數值
                processors = self.value_processors.get(target_field, [])
                current_val = raw_value
                for processor in processors:
                    current_val = processor.process(current_val)
                    
                # 4. 回傳整個 context 作為 highlight 元素
                return {target_field: current_val}, {target_field: context}
                
        return {}, {}



class MappingProfile:
    """
    A collection of generic rules that define how to scrape a specific page type.
    Optionally accepts post_processors to perform derived field calculations.
    """
    def __init__(self, rules: List[BaseRule], post_processors: Optional[List[BasePostProcessor]] = None):
        self.rules = rules
        self.post_processors = post_processors or []


class RuleEngine:
    """
    Executes a MappingProfile against a ChromiumPage.
    Also handles emitting events for the Visualizer automatically!
    """
    def __init__(self, event_bus_emitter: Optional[Callable] = None):
        self.emit_event = event_bus_emitter

    def execute(self, profile: MappingProfile, tab: ChromiumElement, source_id: str, platform_name: str) -> Dict[str, Any]:
        result = {}
        elements_map = {}
        
        # 1. Execute all rules polymorphically
        for rule in profile.rules:
            r_results, r_elements = rule.extract(tab)
            result.update(r_results)
            elements_map.update(r_elements)
            
        # 1.5 Execute post-processors
        for processor in profile.post_processors:
            processor.process(result, elements_map)
                        
        # 2. Emit event for Visualizer if an emitter is provided
        if self.emit_event and elements_map:
            self.emit_event(
                tab=tab,
                elements=elements_map,
                source_id=source_id,
                platform_name=platform_name
            )
            
        return result
