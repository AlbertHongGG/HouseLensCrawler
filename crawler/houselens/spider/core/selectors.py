from abc import ABC, abstractmethod
from typing import List, Optional, Union, Any
from DrissionPage.items import ChromiumElement

class BaseSelector(ABC):
    """
    Base class for all DOM selectors.
    A selector is responsible for finding a specific ChromiumElement within a context element.
    """
    @abstractmethod
    def select(self, context: ChromiumElement) -> Optional[ChromiumElement]:
        pass

    @abstractmethod
    def select_all(self, context: ChromiumElement) -> List[ChromiumElement]:
        pass


class CssSelector(BaseSelector):
    def __init__(self, css: str, timeout: float = 0):
        self.css = css
        self.timeout = timeout

    def select(self, context: ChromiumElement) -> Optional[ChromiumElement]:
        return context.ele(f'css:{self.css}', timeout=self.timeout)

    def select_all(self, context: ChromiumElement) -> List[ChromiumElement]:
        return context.eles(f'css:{self.css}', timeout=self.timeout)


class XPathSelector(BaseSelector):
    def __init__(self, xpath: str, timeout: float = 0):
        self.xpath = xpath
        self.timeout = timeout

    def select(self, context: ChromiumElement) -> Optional[ChromiumElement]:
        return context.ele(f'xpath:{self.xpath}', timeout=self.timeout)

    def select_all(self, context: ChromiumElement) -> List[ChromiumElement]:
        return context.eles(f'xpath:{self.xpath}', timeout=self.timeout)


class TextMatchSelector(BaseSelector):
    def __init__(self, text: str, exact: bool = False, timeout: float = 0):
        self.text = text
        self.exact = exact
        self.timeout = timeout

    def select(self, context: ChromiumElement) -> Optional[ChromiumElement]:
        if self.exact:
            # Using normalize-space() for exact text matching
            return context.ele(f'xpath:.//*[normalize-space(text())="{self.text}"]', timeout=self.timeout)
        else:
            return context.ele(f'text:{self.text}', timeout=self.timeout)

    def select_all(self, context: ChromiumElement) -> List[ChromiumElement]:
        if self.exact:
            return context.eles(f'xpath:.//*[normalize-space(text())="{self.text}"]', timeout=self.timeout)
        else:
            return context.eles(f'text:{self.text}', timeout=self.timeout)


class ParentSelector(BaseSelector):
    """
    Selects the parent of another selector's result.
    Useful when the target data is in the same container as a label.
    """
    def __init__(self, child_selector: BaseSelector, levels: int = 1):
        self.child_selector = child_selector
        self.levels = levels

    def select(self, context: ChromiumElement) -> Optional[ChromiumElement]:
        child = self.child_selector.select(context)
        if not child:
            return None
        parent = child
        for _ in range(self.levels):
            if parent:
                parent = parent.parent()
        return parent

    def select_all(self, context: ChromiumElement) -> List[ChromiumElement]:
        children = self.child_selector.select_all(context)
        parents = []
        for child in children:
            parent = child
            for _ in range(self.levels):
                if parent:
                    parent = parent.parent()
            if parent:
                parents.append(parent)
        return parents



