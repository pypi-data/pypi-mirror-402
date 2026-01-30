import aiohttp
from typing import Optional


class Auth:
    def __init__(self, token: str):
        self.token = token
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        if not self._session or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session
    
    async def get_socket_token(self) -> str:
        session = await self._get_session()
        headers = {"Authorization": f"Bot {self.token}"}
        async with session.get("https://hubber.cc/api/bot/socket-token", headers=headers) as resp:
            data = await resp.json()
            return data["token"]
    
    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()
