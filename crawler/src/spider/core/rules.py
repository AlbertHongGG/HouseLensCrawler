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


class MappingProfile:
    """
    A collection of rules that define how to scrape a specific page type.
    """
    def __init__(self, rules: List[FieldRule], blocks: Optional[List[BlockRule]] = None):
        self.rules = rules
        self.blocks = blocks or []


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
                for field in block.fields:
                    val, ele = field.extract(container)
                    result[field.name] = val
                    if ele:
                        elements_map[field.name] = ele
                        
        # 3. Emit event for Visualizer if an emitter is provided
        if self.emit_event and elements_map:
            self.emit_event(
                tab=tab,
                elements=elements_map,
                source_id=source_id,
                platform_name=platform_name
            )
            
        return result
