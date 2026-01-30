from typing import Optional


class Author:
    def __init__(self, data: dict):
        self.id = data.get("user_id")
        self.username = data.get("username")
        self.avatar = data.get("avatar")
        self.avatar_color = data.get("avatar_color")
        self.display_badge = data.get("display_badge")
        self.role_color = data.get("role_color")
    
    @property
    def avatar_url(self) -> Optional[str]:
        if self.avatar:
            return f"https://hubber.cc{self.avatar}"
        return None
    
    def __str__(self) -> str:
        return self.username or str(self.id)
