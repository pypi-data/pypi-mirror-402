from typing import Optional, List, Dict, Any
from enum import Enum


class ButtonStyle(str, Enum):
    PRIMARY = "primary"
    SECONDARY = "secondary"
    SUCCESS = "success"
    DANGER = "danger"
    LINK = "link"


class Button:
    def __init__(self, label: str, style: ButtonStyle = ButtonStyle.PRIMARY, custom_id: Optional[str] = None, url: Optional[str] = None):
        self.label = label[:80]
        self.style = style
        self.custom_id = custom_id[:100] if custom_id else None
        self.url = url
    
    def to_dict(self) -> Dict[str, Any]:
        data = {
            "type": 2,
            "style": self.style.value,
            "label": self.label
        }
        if self.style == ButtonStyle.LINK:
            if self.url:
                data["url"] = self.url
        else:
            if self.custom_id:
                data["custom_id"] = self.custom_id
        return data


class ActionRow:
    def __init__(self):
        self.buttons: List[Button] = []
    
    def add_button(self, label: str, style: ButtonStyle = ButtonStyle.PRIMARY, custom_id: Optional[str] = None, url: Optional[str] = None):
        if len(self.buttons) < 5:
            self.buttons.append(Button(label, style, custom_id, url))
        return self
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": 1,
            "components": [btn.to_dict() for btn in self.buttons]
        }
