"""General internet helpers.

Requires the 'web' extra: pip install wardy-utils[web]
"""

from __future__ import annotations

import logging
import threading
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path
from typing import Final, Literal, overload

from pydantic_settings import BaseSettings, SettingsConfigDict

try:
    from hishel import AsyncSqliteStorage, FilterPolicy, SyncSqliteStorage
    from hishel.httpx import AsyncCacheClient, SyncCacheClient
except ImportError as e:  # pragma: no cover
    msg = "hishel/httpx required for wardy_utils.web. Install: pip install wardy-utils[web]"
    raise ImportError(msg) from e

logging.getLogger("httpcore").setLevel(logging.INFO)
# hishel INFO level is appropriate - DEBUG is verbose about cached responses
logging.getLogger("hishel").setLevel(logging.INFO)

# ----- Constants -----

CACHE_TTL_DEFAULT_SECONDS: Final = timedelta(minutes=30).total_seconds()
HTTP_TIMEOUT_SECONDS: Final = timedelta(seconds=45).total_seconds()


class WebSettings(BaseSettings):
    """Environment-driven defaults for HTTP clients."""

    cache_dir: str | Path = ""
    cache_filename: str = "wardy_cache.db"
    cache_ttl: float = CACHE_TTL_DEFAULT_SECONDS
    timeout: float = HTTP_TIMEOUT_SECONDS
    force_cache: bool = False
    http2: bool = True

    model_config = SettingsConfigDict(env_prefix="WARDY_UTILS_WEB_", case_sensitive=False)


@dataclass(frozen=True)
class ClientConfig:
    """Configuration for a cached HTTP client."""

    sync: bool
    force: bool
    cache_db: str
    ttl: float
    timeout: float
    http2: bool


_CLIENTS: dict[ClientConfig, SyncCacheClient | AsyncCacheClient] = {}
_CLIENTS_LOCK = threading.Lock()


def _resolve_config(
    *,
    sync: bool,
    force: bool | None,
    cache_dir: str | None,
    ttl: float | None,
    timeout: float | None,
    http2: bool | None,
) -> ClientConfig:
    env = WebSettings()

    resolved_ttl = ttl if ttl is not None else env.cache_ttl
    resolved_timeout = timeout if timeout is not None else env.timeout
    resolved_force = force if force is not None else env.force_cache
    resolved_http2 = http2 if http2 is not None else env.http2

    resolved_cache_dir = cache_dir if cache_dir is not None else env.cache_dir

    if resolved_cache_dir:
        cache_path = Path(resolved_cache_dir)
        cache_path.mkdir(parents=True, exist_ok=True)
        cache_db = str(cache_path / env.cache_filename)
    else:
        cache_db = ":memory:"

    return ClientConfig(
        sync=sync,
        force=resolved_force,
        cache_db=cache_db,
        ttl=resolved_ttl,
        timeout=resolved_timeout,
        http2=resolved_http2,
    )


def _build_client(config: ClientConfig) -> SyncCacheClient | AsyncCacheClient:
    storage: SyncSqliteStorage | AsyncSqliteStorage
    if config.cache_db != ":memory:":
        Path(config.cache_db).touch(exist_ok=True)

    if config.sync:
        storage = SyncSqliteStorage(database_path=config.cache_db, default_ttl=config.ttl)
    else:
        storage = AsyncSqliteStorage(database_path=config.cache_db, default_ttl=config.ttl)

    policy = FilterPolicy() if config.force else None
    client_class = SyncCacheClient if config.sync else AsyncCacheClient

    return client_class(
        follow_redirects=True,
        storage=storage,
        policy=policy,
        timeout=config.timeout,
        http2=config.http2,
    )


# ----- Handle httpx client and hishel caching -----


@overload
def cached_client() -> SyncCacheClient: ...
@overload
def cached_client(
    *,
    sync: Literal[True],
    force: bool | None = ...,
    ttl: float | None = ...,
    timeout: float | None = ...,
    cache_dir: str | None = ...,
    http2: bool | None = ...,
) -> SyncCacheClient: ...
@overload
def cached_client(
    *,
    sync: Literal[False],
    force: bool | None = ...,
    ttl: float | None = ...,
    timeout: float | None = ...,
    cache_dir: str | None = ...,
    http2: bool | None = ...,
) -> AsyncCacheClient: ...


def cached_client(
    *,
    sync: bool = True,
    force: bool | None = None,
    ttl: float | None = None,
    timeout: float | None = None,
    cache_dir: str | None = None,
    http2: bool | None = None,
) -> SyncCacheClient | AsyncCacheClient:
    """Return a cached HTTPX client (sync or async).

    By default, uses in-memory cache (safe for production/FastAPI).
    In test environments, set WARDY_UTILS_CACHE_DIR to enable
    persistent filesystem cache across test runs.

    Args:
        sync (bool): Whether to use sync or async client. Defaults to True.
        force (bool | None): Whether to force cache regardless of origin headers.
                     Uses FilterPolicy which ignores cache-control directives.
                     Defaults to env WARDY_UTILS_FORCE_CACHE or False.
        ttl (float | None): Time to live for cache entries in seconds.
                     Defaults to env WARDY_UTILS_CACHE_TTL or 30 minutes.
        timeout (float | None): Timeout for requests in seconds.
                     Defaults to env WARDY_UTILS_TIMEOUT or 45 seconds.
        cache_dir (str | None): Directory to use for persistent cache. If not set,
                     uses env WARDY_UTILS_CACHE_DIR or in-memory cache.
        http2 (bool | None): Toggle HTTP/2 support. Defaults to env WARDY_UTILS_HTTP2 or True.

    Returns:
        SyncCacheClient | AsyncCacheClient: A cached HTTPX client.
    """
    config = _resolve_config(
        sync=sync, force=force, cache_dir=cache_dir, ttl=ttl, timeout=timeout, http2=http2
    )

    with _CLIENTS_LOCK:
        client = _CLIENTS.get(config)

        if client is None or getattr(client, "is_closed", False):
            client = _build_client(config)
            _CLIENTS[config] = client

    return client


sync_client = cached_client(sync=True)
sync_force_client = cached_client(sync=True, force=True)
async_client = cached_client(sync=False)
async_force_client = cached_client(sync=False, force=True)
