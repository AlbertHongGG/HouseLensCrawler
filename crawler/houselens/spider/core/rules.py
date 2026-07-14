import logging
import re
from abc import ABC, abstractmethod
from typing import List, Optional, Any, Dict, Callable, Tuple, Union
from DrissionPage.items import ChromiumElement
from .selectors import BaseSelector
from .processors import BaseProcessor

class BaseRule(ABC):
    """
    Abstract base class for all rules.
    Every rule must implement `extract` which returns a tuple of:
    (Dict of extracted field names and values, Dict of field names and source elements)
    """
    @abstractmethod
    def extract(self, context: ChromiumElement) -> Tuple[Dict[str, Any], Dict[str, ChromiumElement]]:
        pass


class FieldRule(BaseRule):
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


class BlockRule(BaseRule):
    """
    Defines a reusable block (Composite Rule) that shares a common container.
    """
    def __init__(self, name: str, container_selector: BaseSelector, rules: List[BaseRule]):
        self.name = name
        self.container_selector = container_selector
        self.rules = rules
        
    def extract(self, context: ChromiumElement) -> Tuple[Dict[str, Any], Dict[str, ChromiumElement]]:
        container = self.container_selector.select(context)
        if not container:
            print(f"[DEBUG] Block '{self.name}' container NOT FOUND!")
            return {}, {}
            
        print(f"[DEBUG] Block '{self.name}' container FOUND!")
        results = {}
        elements = {}
        
        for rule in self.rules:
            r_results, r_elements = rule.extract(container)
            results.update(r_results)
            elements.update(r_elements)
            
        return results, elements


class KeyValueRule(BaseRule):
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
        text = re.sub(r'<[^>]+>', '', html)
        text = text.replace(' ', '').replace('\n', '').strip()
        text = text.split('：')[0].split(':')[0]
        return text

    def _clean_value(self, html: str) -> str:
        text = re.sub(r'<[^>]+>', '', html)
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
                
                for mapped_key_name, target_field in self.key_mapping.items():
                    if mapped_key_name in clean_key:
                        raw_value = self._clean_value(value_ele.html)
                        
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
    A collection of generic rules that define how to scrape a specific page type.
    """
    def __init__(self, rules: List[BaseRule]):
        self.rules = rules


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
                        
        # 2. Emit event for Visualizer if an emitter is provided
        if self.emit_event and elements_map:
            self.emit_event(
                tab=tab,
                elements=elements_map,
                source_id=source_id,
                platform_name=platform_name
            )
            
        return result
