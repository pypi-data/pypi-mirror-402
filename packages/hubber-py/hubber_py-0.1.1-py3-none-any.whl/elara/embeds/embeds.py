from typing import Optional, List, Dict, Any
from datetime import datetime


class EmbedAuthor:
    def __init__(self, name: str, icon_url: Optional[str] = None, url: Optional[str] = None):
        self.name = name[:256]
        self.icon_url = icon_url
        self.url = url
    
    def to_dict(self) -> Dict[str, Any]:
        data = {"name": self.name}
        if self.icon_url:
            data["icon_url"] = self.icon_url
        if self.url:
            data["url"] = self.url
        return data


class EmbedField:
    def __init__(self, name: str, value: str, inline: bool = False):
        self.name = name[:256]
        self.value = value[:1024]
        self.inline = inline
    
    def to_dict(self) -> Dict[str, Any]:
        return {"name": self.name, "value": self.value, "inline": self.inline}


class EmbedFooter:
    def __init__(self, text: str, icon_url: Optional[str] = None):
        self.text = text[:2048]
        self.icon_url = icon_url
    
    def to_dict(self) -> Dict[str, Any]:
        data = {"text": self.text}
        if self.icon_url:
            data["icon_url"] = self.icon_url
        return data


class Embed:
    def __init__(self, title: Optional[str] = None, description: Optional[str] = None, color: Optional[str] = None, url: Optional[str] = None):
        self.title = title[:256] if title else None
        self.description = description[:4096] if description else None
        self.color = color
        self.url = url
        self._author: Optional[EmbedAuthor] = None
        self._fields: List[EmbedField] = []
        self._footer: Optional[EmbedFooter] = None
        self._thumbnail: Optional[str] = None
        self._image: Optional[str] = None
        self._timestamp: Optional[str] = None
    
    def set_author(self, name: str, icon_url: Optional[str] = None, url: Optional[str] = None):
        self._author = EmbedAuthor(name, icon_url, url)
        return self
    
    def add_field(self, name: str, value: str, inline: bool = False):
        if len(self._fields) < 25:
            self._fields.append(EmbedField(name, value, inline))
        return self
    
    def set_footer(self, text: str, icon_url: Optional[str] = None):
        self._footer = EmbedFooter(text, icon_url)
        return self
    
    def set_thumbnail(self, url: str):
        self._thumbnail = url
        return self
    
    def set_image(self, url: str):
        self._image = url
        return self
    
    def set_color(self, color: str):
        self.color = color
        return self
    
    def set_timestamp(self, timestamp: Optional[datetime] = None):
        if timestamp is None:
            timestamp = datetime.utcnow()
        self._timestamp = timestamp.isoformat() + "Z"
        return self
    
    def to_dict(self) -> Dict[str, Any]:
        data = {}
        if self.title:
            data["title"] = self.title
        if self.description:
            data["description"] = self.description
        if self.color:
            data["color"] = self.color
        if self.url:
            data["url"] = self.url
        if self._author:
            data["author"] = self._author.to_dict()
        if self._fields:
            data["fields"] = [f.to_dict() for f in self._fields]
        if self._footer:
            data["footer"] = self._footer.to_dict()
        if self._thumbnail:
            data["thumbnail"] = {"url": self._thumbnail}
        if self._image:
            data["image"] = {"url": self._image}
        if self._timestamp:
            data["timestamp"] = self._timestamp
        return data
