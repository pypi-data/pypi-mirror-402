import asyncio
import threading
import time
from typing import Optional

import redis
from redis.asyncio import Redis as AsyncRedis
from redis.asyncio.lock import Lock as NativeAsyncRedisLock
from redis.client import Lock as NativeRedisLock
from redis.client import Redis
from redis.exceptions import LockError

from recurvedata.config import REDIS_LOCK_URL


class RedisLock:
    """
    Redis-based distributed lock implementation using redis.lock

    Usage:
    ```
    with RedisLock("my_lock_name", expire=60) as lock:
        if lock.acquired:
            # Execute code that needs lock protection
            pass
        else:
            # Failed to acquire lock
            pass
    ```

    Or manage manually:
    ```
    lock = RedisLock("my_lock_name")
    if lock.acquire():
        try:
            # Execute code that needs lock protection
            pass
        finally:
            lock.release()
    ```

    You can also extend the lock expiration time:
    ```
    lock = RedisLock("my_lock_name", expire=60)
    if lock.acquire():
        try:
            # Start some long operation
            # ...
            # Extend the lock if operation takes longer than expected
            lock.extend(additional_time=60)
            # Continue operation
            # ...
        finally:
            lock.release()
    ```

    For long-running operations with unknown duration, you can use auto-extend:
    ```
    with RedisLock("my_lock_name", expire=60, auto_extend=True) as lock:
        if lock.acquired:
            # Execute long-running code, lock will be automatically extended
            # until the operation completes or the lock is released
            pass
    ```
    """

    def __init__(
        self,
        name: str,
        expire: int = 60,
        timeout: int = 0,
        sleep_interval: float = 0.1,
        redis_client: Optional[Redis] = None,
        redis_url: Optional[str] = REDIS_LOCK_URL,
        auto_extend: bool = False,
        extend_interval: Optional[int] = None,
    ):
        """
        Initialize Redis lock

        Args:
            name: Lock name, must be unique
            expire: Lock expiration time (seconds), prevents deadlock
            timeout: Lock acquisition timeout (seconds), 0 means try only once
            sleep_interval: Sleep interval (seconds)
            redis_client: Optional Redis client, if not provided will create from REDIS_URL
            auto_extend: Whether to automatically extend the lock while it's held
            extend_interval: Interval (seconds) to extend the lock, defaults to expire/3
        """
        self.name = f"recurve:lock:{name}"
        self.expire = expire
        self.timeout = timeout
        self.sleep_interval = sleep_interval
        self.acquired = False
        self.auto_extend = auto_extend
        self.extend_interval = extend_interval or max(1, int(expire / 3))
        self._extend_thread = None
        self._stop_extend = threading.Event()
        self._lock_token = None  # Store the lock token for cross-thread access

        if redis_client is not None:
            self.redis = redis_client
        else:
            self.redis = redis.from_url(redis_url)

        # Create the native Redis lock
        self.lock: NativeRedisLock = self.redis.lock(self.name, timeout=self.expire, sleep=self.sleep_interval)

    def _extend_lock_periodically(self):
        """Background thread that periodically extends the lock"""
        while not self._stop_extend.is_set():
            # Sleep for the extend interval
            for _ in range(int(self.extend_interval / self.sleep_interval)):  # Check stop flag more frequently
                if self._stop_extend.is_set():
                    return
                time.sleep(self.sleep_interval)

            # Extend the lock if we still have it
            if self.acquired:
                try:
                    # Directly extend the lock using Redis commands instead of the lock.extend method
                    # This avoids the thread-local token issue
                    success = self._extend_lock_directly()
                    if not success:
                        # If extension fails, stop the thread
                        self._stop_extend.set()
                except Exception:
                    # If any exception occurs, stop the thread
                    self._stop_extend.set()

    def _extend_lock_directly(self) -> bool:
        """
        Extend the lock directly using Redis commands

        Returns:
            bool: Whether successfully extended the lock
        """
        if not self.acquired or not self._lock_token:
            return False

        try:
            # Use Redis PEXPIRE command to extend the lock if the token matches
            script = """
            if redis.call('get', KEYS[1]) == ARGV[1] then
                return redis.call('pexpire', KEYS[1], ARGV[2])
            else
                return 0
            end
            """
            # Convert seconds to milliseconds for pexpire
            extend_time_ms = int(self.expire * 1000)
            result = self.redis.eval(script, 1, self.name, self._lock_token, extend_time_ms)
            return bool(result)
        except Exception:
            return False

    def _start_extend_thread(self):
        """Start the background thread to extend the lock periodically"""
        if not self._extend_thread:
            self._stop_extend.clear()
            self._extend_thread = threading.Thread(
                target=self._extend_lock_periodically, daemon=True  # Make it a daemon so it doesn't block program exit
            )
            self._extend_thread.start()

    def _stop_extend_thread(self):
        """Stop the background thread that extends the lock"""
        if self._extend_thread:
            self._stop_extend.set()
            if self._extend_thread.is_alive():
                self._extend_thread.join(timeout=1.0)  # Wait for thread to finish
            self._extend_thread = None

    def acquire(self) -> bool:
        """
        Try to acquire the lock

        Returns:
            bool: Whether successfully acquired the lock
        """
        if self.timeout > 0:
            # With timeout
            try:
                self.acquired = self.lock.acquire(blocking=True, blocking_timeout=self.timeout)
            except redis.exceptions.LockError:
                self.acquired = False
        else:
            # Without timeout (try once)
            try:
                self.acquired = self.lock.acquire(blocking=False)
            except redis.exceptions.LockError:
                self.acquired = False

        # Store the lock token for cross-thread access if acquired
        if self.acquired:
            # Access the thread-local token from the lock
            self._lock_token = self.lock.local.token

            # If auto_extend is enabled, start the extend thread
            if self.auto_extend:
                self._start_extend_thread()

        return self.acquired

    def release(self) -> bool:
        """
        Release the lock

        Returns:
            bool: Whether successfully released the lock
        """
        if not self.acquired:
            return False

        # Stop the extend thread if it's running
        self._stop_extend_thread()

        try:
            self.lock.release()
            self.acquired = False
            self._lock_token = None  # Clear the token
            return True
        except redis.exceptions.LockError:
            return False

    def extend(self, additional_time: Optional[int] = None) -> bool:
        """
        Extend the lock's expiration time

        Args:
            additional_time: Additional seconds to extend the lock.
                             If None, uses the original expire time.

        Returns:
            bool: Whether successfully extended the lock
        """
        if not self.acquired:
            return False

        try:
            # If additional_time is not provided, use the original expire time
            extend_time = additional_time if additional_time is not None else self.expire

            # Try to use the lock's extend method first
            try:
                success = self.lock.extend(additional_time=extend_time)
                return success
            except AttributeError:
                # Fallback for older redis-py versions that don't support extend
                # or if we're in a different thread
                return self._extend_lock_directly()

        except redis.exceptions.LockError:
            return False

    def __enter__(self) -> "RedisLock":
        self.acquire()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if self.acquired:
            self.release()


class AsyncRedisLock:
    """
    Redis-based distributed lock implementation using redis.lock (async version)

    Usage:
    ```
    async with AsyncRedisLock("my_lock_name", expire=60) as lock:
        if lock.acquired:
            # Execute code that needs lock protection
            pass
        else:
            # Failed to acquire lock
            pass
    ```

    Or manage manually:
    ```
    lock = AsyncRedisLock("my_lock_name")
    if await lock.acquire():
        try:
            # Execute code that needs lock protection
            pass
        finally:
            await lock.release()
    ```

    You can also extend the lock expiration time:
    ```
    lock = AsyncRedisLock("my_lock_name", expire=60)
    if await lock.acquire():
        try:
            # Start some long operation
            # ...
            # Extend the lock if operation takes longer than expected
            await lock.extend(additional_time=60)
            # Continue operation
            # ...
        finally:
            await lock.release()
    ```

    For long-running operations with unknown duration, you can use auto-extend:
    ```
    async with AsyncRedisLock("my_lock_name", expire=60, auto_extend=True) as lock:
        if lock.acquired:
            # Execute long-running code, lock will be automatically extended
            # until the operation completes or the lock is released
            pass
    ```
    """

    def __init__(
        self,
        name: str,
        expire: int = 60,
        timeout: int = 0,
        sleep_interval: float = 0.1,
        redis_client: Optional[AsyncRedis] = None,
        redis_url: Optional[str] = REDIS_LOCK_URL,
        auto_extend: bool = False,
        extend_interval: Optional[int] = None,
    ):
        """
        Initialize Redis lock

        Args:
            name: Lock name, must be unique
            expire: Lock expiration time (seconds), prevents deadlock
            timeout: Lock acquisition timeout (seconds), 0 means try only once
            sleep_interval: Sleep interval (seconds)
            redis_client: Optional Redis client, if not provided will create from REDIS_URL
            auto_extend: Whether to automatically extend the lock while it's held
            extend_interval: Interval (seconds) to extend the lock, defaults to expire/3
        """
        self.name = f"recurve:lock:{name}"
        self.expire = expire
        self.timeout = timeout
        self.sleep_interval = sleep_interval
        self.acquired = False
        self.auto_extend = auto_extend
        self.extend_interval = extend_interval or max(1, int(expire / 3))
        self._extend_task = None
        self._stop_extend = asyncio.Event()
        self._lock_token = None

        self.redis = redis_client if redis_client is not None else AsyncRedis.from_url(redis_url)
        self.lock: NativeAsyncRedisLock = self.redis.lock(self.name, timeout=self.expire, sleep=self.sleep_interval)

    async def _extend_lock_periodically(self):
        """Background task that periodically extends the lock"""
        while not self._stop_extend.is_set():
            try:
                await asyncio.sleep(self.extend_interval)
                if self.acquired:
                    success = await self._extend_lock_directly()
                    if not success:
                        self._stop_extend.set()
            except Exception:
                self._stop_extend.set()

    async def _extend_lock_directly(self) -> bool:
        """
        Extend the lock directly using Redis commands

        Returns:
            bool: Whether successfully extended the lock
        """
        if not self.acquired or not self._lock_token:
            return False

        try:
            script = """
            if redis.call('get', KEYS[1]) == ARGV[1] then
                return redis.call('pexpire', KEYS[1], ARGV[2])
            else
                return 0
            end
            """
            extend_time_ms = int(self.expire * 1000)
            result = await self.redis.eval(script, 1, self.name, self._lock_token, extend_time_ms)
            return bool(result)
        except Exception:
            return False

    def _start_extend_task(self):
        """Start the background task to extend the lock periodically"""
        if not self._extend_task:
            self._stop_extend.clear()
            self._extend_task = asyncio.create_task(self._extend_lock_periodically())

    async def _stop_extend_task(self):
        """Stop the background task that extends the lock"""
        if self._extend_task:
            self._stop_extend.set()
            await self._extend_task
            self._extend_task = None

    async def acquire(self) -> bool:
        """
        Try to acquire the lock

        Returns:
            bool: Whether successfully acquired the lock
        """
        try:
            if self.timeout > 0:
                self.acquired = await self.lock.acquire(blocking=True, blocking_timeout=self.timeout)
            else:
                self.acquired = await self.lock.acquire(blocking=False)

            if self.acquired:
                self._lock_token = self.lock.local.token
                if self.auto_extend:
                    self._start_extend_task()

            return self.acquired
        except LockError:
            self.acquired = False
            return False

    async def release(self) -> bool:
        """
        Release the lock

        Returns:
            bool: Whether successfully released the lock
        """
        if not self.acquired:
            return False

        await self._stop_extend_task()

        try:
            await self.lock.release()
            self.acquired = False
            self._lock_token = None
            return True
        except LockError:
            return False

    async def extend(self, additional_time: Optional[int] = None) -> bool:
        """
        Extend the lock's expiration time

        Args:
            additional_time: Additional seconds to extend the lock.
                           If None, uses the original expire time.

        Returns:
            bool: Whether successfully extended the lock
        """
        if not self.acquired:
            return False

        try:
            extend_time = additional_time if additional_time is not None else self.expire
            try:
                return await self.lock.extend(additional_time=extend_time)
            except AttributeError:
                return await self._extend_lock_directly()
        except LockError:
            return False

    async def __aenter__(self) -> "AsyncRedisLock":
        await self.acquire()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        if self.acquired:
            await self.release()
