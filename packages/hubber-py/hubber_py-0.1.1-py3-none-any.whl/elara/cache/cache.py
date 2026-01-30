import asyncio
from typing import Any, Optional, Dict, TypeVar, Generic, Callable, Set
from collections import OrderedDict
from time import perf_counter
from enum import Enum

T = TypeVar('T')


class EvictionPolicy(str, Enum):
    LRU = "lru"
    LFU = "lfu"
    FIFO = "fifo"


class CacheEntry(Generic[T]):
    __slots__ = ('value', 'expires_at', 'created_at', 'access_count', 'last_access')
    
    def __init__(self, value: T, ttl: Optional[float]):
        self.value = value
        now = perf_counter()
        self.expires_at = now + ttl if ttl else None
        self.created_at = now
        self.last_access = now
        self.access_count = 0
    
    def is_expired(self) -> bool:
        return self.expires_at is not None and perf_counter() > self.expires_at
    
    def touch(self) -> None:
        self.last_access = perf_counter()
        self.access_count += 1


class Cache:
    def __init__(
        self,
        max_size: int = 1000,
        default_ttl: Optional[float] = None,
        eviction_policy: EvictionPolicy = EvictionPolicy.LRU,
        auto_cleanup: bool = False,
        cleanup_interval: float = 60.0
    ):
        self._store: OrderedDict[str, CacheEntry] = OrderedDict()
        self._max_size = max_size
        self._default_ttl = default_ttl
        self._eviction_policy = eviction_policy
        self._lock = asyncio.Lock()
        self._hits = 0
        self._misses = 0
        self._evictions = 0
        self._cleanup_task: Optional[asyncio.Task] = None
        self._namespaces: Dict[str, Set[str]] = {}
        self._auto_cleanup_enabled = auto_cleanup
        self._cleanup_interval = cleanup_interval
    
    async def get(self, key: str, default: Any = None) -> Optional[Any]:
        async with self._lock:
            entry = self._store.get(key)
            if not entry:
                self._misses += 1
                return default
            
            if entry.is_expired():
                del self._store[key]
                self._misses += 1
                return default
            
            entry.touch()
            if self._eviction_policy == EvictionPolicy.LRU:
                self._store.move_to_end(key)
            
            self._hits += 1
            return entry.value
    
    async def set(self, key: str, value: Any, ttl: Optional[float] = None, namespace: Optional[str] = None) -> None:
        async with self._lock:
            if key in self._store:
                del self._store[key]
            elif len(self._store) >= self._max_size:
                await self._evict()
            
            self._store[key] = CacheEntry(value, ttl or self._default_ttl)
            
            if namespace:
                if namespace not in self._namespaces:
                    self._namespaces[namespace] = set()
                self._namespaces[namespace].add(key)
    
    async def get_or_set(self, key: str, factory: Callable, ttl: Optional[float] = None) -> Any:
        value = await self.get(key)
        if value is None:
            if asyncio.iscoroutinefunction(factory):
                value = await factory()
            else:
                value = factory()
            await self.set(key, value, ttl)
        return value
    
    async def delete(self, key: str) -> bool:
        async with self._lock:
            entry = self._store.pop(key, None)
            if entry:
                for ns_keys in self._namespaces.values():
                    ns_keys.discard(key)
                return True
            return False
    
    async def delete_namespace(self, namespace: str) -> int:
        async with self._lock:
            if namespace not in self._namespaces:
                return 0
            
            keys = list(self._namespaces[namespace])
            for key in keys:
                self._store.pop(key, None)
            
            del self._namespaces[namespace]
            return len(keys)
    
    async def clear(self) -> None:
        async with self._lock:
            self._store.clear()
            self._namespaces.clear()
    
    async def has(self, key: str) -> bool:
        return await self.get(key) is not None
    
    async def touch(self, key: str, ttl: Optional[float] = None) -> bool:
        async with self._lock:
            entry = self._store.get(key)
            if not entry or entry.is_expired():
                return False
            
            if ttl is not None:
                entry.expires_at = perf_counter() + ttl
            entry.touch()
            return True
    
    async def cleanup_expired(self) -> int:
        async with self._lock:
            expired = [k for k, v in self._store.items() if v.is_expired()]
            for key in expired:
                del self._store[key]
                for ns_keys in self._namespaces.values():
                    ns_keys.discard(key)
            return len(expired)
    
    async def _evict(self) -> None:
        if not self._store:
            return
        
        if self._eviction_policy == EvictionPolicy.LRU:
            key = next(iter(self._store))
        elif self._eviction_policy == EvictionPolicy.LFU:
            key = min(self._store.items(), key=lambda x: x[1].access_count)[0]
        else:
            key = next(iter(self._store))
        
        del self._store[key]
        self._evictions += 1
        
        for ns_keys in self._namespaces.values():
            ns_keys.discard(key)
    
    async def _auto_cleanup(self, interval: float) -> None:
        while True:
            await asyncio.sleep(interval)
            await self.cleanup_expired()
    
    def start_cleanup(self) -> None:
        if self._auto_cleanup_enabled and not self._cleanup_task:
            self._cleanup_task = asyncio.create_task(self._auto_cleanup(self._cleanup_interval))
    
    def size(self) -> int:
        return len(self._store)
    
    def stats(self) -> Dict[str, Any]:
        total = self._hits + self._misses
        hit_rate = (self._hits / total * 100) if total > 0 else 0.0
        return {
            "size": len(self._store),
            "max_size": self._max_size,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": hit_rate,
            "evictions": self._evictions,
            "namespaces": len(self._namespaces)
        }
    
    async def close(self) -> None:
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
    
    async def has(self, key: str) -> bool:
        return await self.get(key) is not None
    
    def size(self) -> int:
        return len(self._store)
