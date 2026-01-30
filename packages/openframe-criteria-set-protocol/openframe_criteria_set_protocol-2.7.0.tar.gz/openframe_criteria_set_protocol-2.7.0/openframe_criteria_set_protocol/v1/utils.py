from typing import Optional

from .types import CriteriaTreeElement, TaskItem, CriteriaTree


def to_color_hex_string(color):
    """
    Convert a color object to a hex string
    """
    if isinstance(color, str):
        return color
    return f"#{color.red:02x}{color.green:02x}{color.blue:02x}"


def find_in_tree(tree: CriteriaTree, code: str) -> Optional[CriteriaTreeElement]:
    """
    Find an element in the criteria tree by its code
    """
    def _search_elements(elements: list[CriteriaTreeElement]):
        for element in elements:
            if element.code == code:
                return element
            if not isinstance(element, TaskItem):
                element = _search_elements(element.items)
                if element is not None:
                    return element
        return None

    return _search_elements(tree.themes)
