import importlib
import sys
from pathlib import Path
from typing import Dict, Optional, TYPE_CHECKING
from .cog import Cog

if TYPE_CHECKING:
    from ..main import Client


class CogManager:
    def __init__(self, client: 'Client'):
        self.client = client
        self._cogs: Dict[str, Cog] = {}
        self._cog_modules: Dict[str, str] = {}
    
    async def load(self, path: str) -> None:
        module_path = path.replace('/', '.').replace('\\', '.').rstrip('.py')
        
        if module_path in self._cog_modules.values():
            raise ValueError(f"Cog from {path} is already loaded")
        
        spec = importlib.util.spec_from_file_location(module_path, path)
        if not spec or not spec.loader:
            raise ImportError(f"Cannot load module from {path}")
        
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_path] = module
        spec.loader.exec_module(module)
        
        setup = getattr(module, 'setup', None)
        if not setup:
            raise ValueError(f"No setup function found in {path}")
        
        await setup(self.client)
    
    async def unload(self, cog_name: str) -> None:
        if cog_name not in self._cogs:
            raise ValueError(f"Cog {cog_name} is not loaded")
        
        cog = self._cogs[cog_name]
        await cog.cog_unload()
        cog._eject(self.client)
        
        module_path = self._cog_modules[cog_name]
        if module_path in sys.modules:
            del sys.modules[module_path]
        
        del self._cogs[cog_name]
        del self._cog_modules[cog_name]
    
    async def reload(self, cog_name: str) -> None:
        if cog_name not in self._cogs:
            raise ValueError(f"Cog {cog_name} is not loaded")
        
        module_path = self._cog_modules[cog_name]
        path = None
        for key, val in self._cog_modules.items():
            if val == module_path:
                path = val.replace('.', '/') + '.py'
                break
        
        await self.unload(cog_name)
        if path:
            await self.load(path)
    
    def get_cog(self, name: str) -> Optional[Cog]:
        return self._cogs.get(name)
    
    def get_cogs(self) -> Dict[str, Cog]:
        return self._cogs.copy()
