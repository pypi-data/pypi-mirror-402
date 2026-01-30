import abc
import functools
import hashlib
import inspect
import json
import pickle
from collections.abc import Callable
from typing import Any, Generic, Protocol, TypeVar, Union, get_type_hints

from loguru import logger
from pydantic import BaseModel
from redis.asyncio import BlockingConnectionPool, Redis

from recurvedata.config import REDIS_CACHE_URL

T = TypeVar("T")
V = TypeVar("V")
KeyBuilderType = Callable[..., str]


class Serializer(Protocol):
    """Protocol for cache serializers."""

    def serialize(self, value: Any) -> bytes:
        """Serialize a value to bytes."""
        ...

    def deserialize(self, data: bytes) -> Any:
        """Deserialize bytes to a value."""
        ...


class PickleSerializer:
    """Default serializer using pickle."""

    def serialize(self, value: Any) -> bytes:
        """Serialize a value to bytes using pickle."""
        # For Pydantic models, convert to dict first to avoid
        # potential issues with pickle serialization across versions
        if isinstance(value, BaseModel):
            return pickle.dumps(value.model_dump())
        return pickle.dumps(value)

    def deserialize(self, data: bytes) -> Any:
        """Deserialize bytes to a value using pickle."""
        return pickle.loads(data)


class JsonSerializer:
    """JSON serializer for text-based values."""

    def serialize(self, value: Any) -> bytes:
        """Serialize a value to bytes using JSON."""
        # For Pydantic models, convert to dict first
        if isinstance(value, BaseModel):
            return value.model_dump_json().encode("utf-8")
        return json.dumps(value).encode("utf-8")

    def deserialize(self, data: bytes) -> Any:
        """Deserialize bytes to a value using JSON."""
        return json.loads(data.decode("utf-8"))


class CacheBackend(abc.ABC, Generic[T]):
    """Abstract base class for cache implementations."""

    _serializer: Serializer

    def hash_key(self, value: Any) -> str:
        """Create a hash from the given value."""
        if isinstance(value, str):
            return hashlib.md5(value.encode()).hexdigest()
        if isinstance(value, dict):
            return hashlib.md5(json.dumps(value, sort_keys=True, default=str).encode()).hexdigest()
        return hashlib.md5(self._serializer.serialize(value)).hexdigest()

    @abc.abstractmethod
    async def get(self, key: str) -> T | None:
        """Get a value from cache.

        Args:
            key: The cache key

        Returns:
            The cached value or None if not found
        """
        pass

    @abc.abstractmethod
    async def set(self, key: str, value: T, ttl: int | None = None, **kwargs: Any) -> bool | None:
        """Set a value in cache.

        Args:
            key: The cache key
            value: The value to cache
            ttl: Time to live in seconds
            kwargs: Optional arguments

        Returns:
            True if set was successful, None if nx=True and key already exists.
        """
        pass

    @abc.abstractmethod
    async def delete(self, key: str) -> None:
        """Delete a value from cache.

        Args:
            key: The cache key
        """
        pass

    @abc.abstractmethod
    async def clear_namespace(self) -> None:
        """Clear all keys in the current namespace."""
        pass


class RedisCache(CacheBackend[T]):
    """Redis-based caching utility for app data."""

    def __init__(
        self,
        namespace: str = "cache",
        serializer: Serializer | None = None,
        redis_url: str = REDIS_CACHE_URL,
        max_connections: int = 100,
    ):
        """Initialize the cache with optional namespace and Redis client.

        Args:
            namespace: The namespace prefix for cache keys
            serializer: Optional serializer for cache values. Defaults to PickleSerializer.
            redis_url: Redis connection URL
            max_connections: Maximum Redis connections
        """
        self.namespace = namespace
        self._redis: Redis | None = None
        self._serializer = serializer or PickleSerializer()
        self._redis_url = redis_url
        self._max_connections = max_connections

    def configure(
        self,
        namespace: str | None = None,
        redis_url: str | None = None,
        max_connections: int | None = None,
        serializer: Serializer | None = None,
    ) -> None:
        """Update the configuration of this Redis cache instance.

        Args:
            namespace: New namespace prefix for cache keys
            redis_url: New Redis connection URL
            max_connections: New maximum Redis connections
            serializer: New serializer for cache values
        """
        if namespace is not None:
            self.namespace = namespace

        if redis_url is not None:
            self._redis_url = redis_url
            # Reset connection so it will be recreated with new settings
            self._redis = None

        if max_connections is not None:
            self._max_connections = max_connections
            # Reset connection so it will be recreated with new settings
            self._redis = None

        if serializer is not None:
            self._serializer = serializer

    async def get_redis(self) -> Redis:
        """Get or create a Redis client."""
        if self._redis is None:
            connection_pool = BlockingConnectionPool.from_url(
                self._redis_url,
                max_connections=self._max_connections,
            )
            self._redis = Redis(connection_pool=connection_pool)
        return self._redis

    def _build_key(self, key: str) -> str:
        """Build a cache key with namespace."""
        return f"{self.namespace}:{key}"

    async def get(self, key: str) -> Any:
        """Get a value from cache.

        Args:
            key: The cache key

        Returns:
            The cached value or None if not found
        """
        redis = await self.get_redis()
        data = await redis.get(self._build_key(key))
        if data:
            return self._serializer.deserialize(data)
        return None

    async def get_and_delete(self, key: str) -> Any:
        """Get a value from cache and delete it."""
        redis = await self.get_redis()
        data = await redis.get(self._build_key(key))
        if data:
            await redis.delete(self._build_key(key))
            return self._serializer.deserialize(data)
        return None

    async def set(self, key: str, value: Any, ttl: int | None = None, **kwargs) -> bool | None:
        """Set a value in cache.

        Args:
            key: The cache key
            value: The value to cache
            ttl: Time to live in seconds
            kwargs: Optional arguments passed to underlying Redis client

        Returns:
            True if set was successful, None if nx=True and key already exists.
        """
        redis = await self.get_redis()
        serialized = self._serializer.serialize(value)
        full_key = self._build_key(key)
        return await redis.set(full_key, serialized, ex=ttl, **kwargs)

    async def delete(self, key: str) -> None:
        """Delete a value from cache.

        Args:
            key: The cache key
        """
        redis = await self.get_redis()
        await redis.delete(self._build_key(key))

    async def clear_namespace(self) -> None:
        """Clear all keys in the current namespace."""
        redis = await self.get_redis()
        pattern = f"{self.namespace}:*"
        cursor = 0
        while True:
            cursor, keys = await redis.scan(cursor, pattern, 100)
            if keys:
                await redis.delete(*keys)
            if cursor == 0:
                break


# Create a default global Redis cache instance
redis_cache = RedisCache()


def cached(
    ttl: int | None = 3600,
    key_builder: KeyBuilderType | None = None,
    cache_backend: CacheBackend | None = None,
    exclude_result_values: list[Any] | None = None,
) -> Callable:
    """Decorator for caching function results.

    Args:
        ttl: Time to live in seconds (default 1 hour)
        key_builder: Optional function to build custom cache keys
        cache_backend: Optional cache backend instance to use
        exclude_result_values: list of values to exclude from the cache key

    Returns:
        Decorated function with caching
    """
    if exclude_result_values is None:
        exclude_result_values = [None]

    def decorator(func: Callable) -> Callable:
        signature = inspect.signature(func)
        return_type = get_type_hints(func).get("return")

        # Use provided cache_backend or the default redis_cache
        cache_instance = cache_backend or redis_cache

        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Build cache key
            if key_builder:
                key = key_builder(*args, **kwargs)
            else:
                # Create a standard key from function args and kwargs
                bound_args = signature.bind(*args, **kwargs)
                bound_args.apply_defaults()
                # Remove request objects which aren't serializable
                args_dict = dict(bound_args.arguments)
                for arg_name, arg_value in list(args_dict.items()):
                    if arg_name == "self" or str(type(arg_value)).startswith("<class '"):
                        args_dict[arg_name] = str(id(arg_value))

                key = cache_instance.hash_key(args_dict)

            key = f"cache:{func.__module__}:{func.__name__}:{key}"

            # Try to get from cache
            cached_value = await cache_instance.get(key)
            if cached_value is not None:
                logger.debug(f"Cache hit for {func.__name__} with key {key}")

                # If the function returns a Pydantic model, validate the cached data
                if return_type and hasattr(return_type, "__origin__") and return_type.__origin__ is Union:
                    # Handle Optional[T] where T is a pydantic model
                    for arg in return_type.__args__:
                        if isinstance(arg, type) and issubclass(arg, BaseModel):
                            if isinstance(cached_value, dict):
                                return arg.model_validate(cached_value)
                            return cached_value
                elif (
                    return_type and isinstance(return_type, type) and issubclass(return_type, BaseModel)
                ):  # noqa: SIM102
                    if isinstance(cached_value, dict):
                        return return_type.model_validate(cached_value)

                return cached_value

            # Cache miss, execute the function
            logger.debug(f"Cache miss for {func.__name__} with key {key}")
            result = await func(*args, **kwargs)

            # Store in cache if it's not None
            if result not in exclude_result_values:
                # Store the value as is - serializers will handle Pydantic models appropriately
                await cache_instance.set(key, result, ttl)

            return result

        return wrapper

    return decorator
