"""
SmartHTTP - 统一的同步/异步 HTTP 客户端

Usage:
    # 同步
    client = SmartHTTP()
    resp = client.get(url)
    resp = client.post(url, json=data)
    
    # 异步
    async with SmartHTTP() as client:
        resp = await client.get(url)
        resp = await client.post(url, json=data)
    
    # 流式（同步）
    with client.stream("POST", url, json=data) as resp:
        for line in resp.iter_lines():
            print(line)
    
    # 流式（异步）
    async with client.stream("POST", url, json=data) as resp:
        async for line in resp.iter_lines():
            print(line)
"""

import asyncio
import random
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional, Iterator, AsyncIterator, Union, Literal

import httpx

try:
    import aiohttp
except ImportError:
    aiohttp = None


# ============ 异常体系 ============

class SmartHTTPError(Exception):
    def __init__(self, message: str, status_code: Optional[int] = None, original_error: Exception = None):
        super().__init__(message)
        self.status_code = status_code
        self.original_error = original_error


class RequestFailed(SmartHTTPError): pass
class NetworkError(SmartHTTPError): pass
class TimeoutError(SmartHTTPError): pass


RETRYABLE_EXCEPTIONS = (
    httpx.TimeoutException,
    httpx.ConnectError,
    httpx.ReadError,
) + ((aiohttp.ClientError,) if aiohttp else ())


# ============ 重试配置 ============

@dataclass
class RetryConfig:
    """重试配置"""
    total: int = 3  # 最大重试次数
    status_forcelist: tuple = (500, 502, 503, 504)  # 需要重试的状态码
    allowed_methods: tuple = ("GET", "POST", "HEAD", "OPTIONS", "PUT", "DELETE")  # 允许重试的方法
    backoff_factor: float = 0.1  # 退避因子


# ============ 统一响应包装器 ============

class SmartResponse:
    """统一的响应对象，屏蔽 httpx/aiohttp 差异"""
    
    def __init__(self, raw_response: Any, backend: str = "httpx"):
        self._raw = raw_response
        self._backend = backend
        self._text_cache = None
    
    @property
    def status_code(self) -> int:
        if self._backend == "httpx":
            return self._raw.status_code
        return self._raw.status  # aiohttp
    
    @property
    def headers(self) -> Dict[str, str]:
        return dict(self._raw.headers)
    
    @property
    def text(self) -> str:
        if self._text_cache is not None:
            return self._text_cache
        if self._backend == "httpx":
            self._text_cache = self._raw.text
        else:
            raise RuntimeError("For aiohttp, use 'await response.text_async()' or access after awaiting")
        return self._text_cache
    
    async def text_async(self) -> str:
        if self._text_cache is not None:
            return self._text_cache
        if self._backend == "httpx":
            self._text_cache = self._raw.text
        else:
            self._text_cache = await self._raw.text()
        return self._text_cache
    
    def json(self) -> Any:
        if self._backend == "httpx":
            return self._raw.json()
        raise RuntimeError("For aiohttp, use 'await response.json_async()'")
    
    async def json_async(self) -> Any:
        if self._backend == "httpx":
            return self._raw.json()
        return await self._raw.json()
    
    @property
    def content(self) -> bytes:
        if self._backend == "httpx":
            return self._raw.content
        raise RuntimeError("For aiohttp, use 'await response.content_async()'")
    
    async def content_async(self) -> bytes:
        if self._backend == "httpx":
            return self._raw.content
        return await self._raw.read()


# ============ 流式响应包装器 ============

class StreamResponse:
    """同步流式响应"""
    
    def __init__(self, ctx_manager):
        self._ctx = ctx_manager
        self._response = None
    
    def __enter__(self):
        self._response = self._ctx.__enter__()
        return self
    
    def __exit__(self, *args):
        return self._ctx.__exit__(*args)
    
    @property
    def status_code(self) -> int:
        return self._response.status_code
    
    @property
    def headers(self) -> Dict[str, str]:
        return dict(self._response.headers)
    
    def iter_lines(self) -> Iterator[str]:
        return self._response.iter_lines()
    
    def iter_bytes(self, chunk_size: int = 1024) -> Iterator[bytes]:
        return self._response.iter_bytes(chunk_size=chunk_size)


class AsyncStreamResponse:
    """异步流式响应"""
    
    def __init__(self, ctx_manager_or_response: Any, backend: str = "httpx"):
        self._ctx = ctx_manager_or_response
        self._response = None
        self._backend = backend
    
    async def __aenter__(self):
        if self._backend == "httpx":
            self._response = await self._ctx.__aenter__()
        else:
            # aiohttp 直接就是 response
            self._response = self._ctx
        return self
    
    async def __aexit__(self, *args):
        if self._backend == "httpx":
            await self._ctx.__aexit__(*args)
        else:
            self._response.release()
    
    @property
    def status_code(self) -> int:
        if self._backend == "httpx":
            return self._response.status_code
        return self._response.status
    
    @property
    def headers(self) -> Dict[str, str]:
        return dict(self._response.headers)
    
    async def iter_lines(self) -> AsyncIterator[str]:
        if self._backend == "httpx":
            async for line in self._response.aiter_lines():
                yield line
        else:
            # aiohttp 需要手动处理行分割
            buffer = b""
            async for chunk in self._response.content.iter_any():
                buffer += chunk
                while b"\n" in buffer:
                    line, buffer = buffer.split(b"\n", 1)
                    yield line.decode(errors="ignore")
            if buffer:
                yield buffer.decode(errors="ignore")
    
    async def iter_bytes(self, chunk_size: int = 1024) -> AsyncIterator[bytes]:
        if self._backend == "httpx":
            async for chunk in self._response.aiter_bytes(chunk_size=chunk_size):
                yield chunk
        else:
            async for chunk in self._response.content.iter_chunked(chunk_size):
                yield chunk


# ============ 双模式流上下文 ============

class DualModeStream:
    """
    支持同步和异步两种模式的流上下文管理器。
    用法：
        with client.stream(...) as resp:    # 同步
        async with client.stream(...) as resp:  # 异步
    """
    
    def __init__(self, client: "SmartHTTP", method: str, url: str, **kwargs):
        self._client = client
        self._method = method
        self._url = url
        self._kwargs = kwargs
        self._sync_ctx = None
        self._async_ctx = None
    
    # 同步上下文
    def __enter__(self):
        if self._client._backend != "httpx":
            raise RuntimeError("Sync streaming only supported with httpx backend")
        self._sync_ctx = self._client._sync_client.stream(self._method, self._url, **self._kwargs)
        return StreamResponse(self._sync_ctx).__enter__()
    
    def __exit__(self, *args):
        if self._sync_ctx:
            return self._sync_ctx.__exit__(*args)
    
    # 异步上下文
    async def __aenter__(self):
        if self._client._backend == "httpx":
            self._async_ctx = self._client._async_client.stream(self._method, self._url, **self._kwargs)
            resp = AsyncStreamResponse(self._async_ctx, "httpx")
        else:
            session = await self._client._get_aiohttp_session()
            self._async_ctx = await session.request(self._method, self._url, **self._kwargs)
            resp = AsyncStreamResponse(self._async_ctx, "aiohttp")
        await resp.__aenter__()
        return resp
    
    async def __aexit__(self, *args):
        if self._client._backend == "httpx" and self._async_ctx:
            await self._async_ctx.__aexit__(*args)
        elif self._async_ctx:
            self._async_ctx.release()


# ============ 主客户端类 ============

class SmartHTTP:
    """
    统一的同步/异步 HTTP 客户端。
    
    Args:
        base_url: 基础 URL
        backend: 后端引擎 ("httpx" 或 "aiohttp")
        connect_timeout: 连接超时（秒）
        read_timeout: 读取超时（秒）
        write_timeout: 写入超时（秒）
        max_connections: 最大连接数
        headers: 默认请求头
    """
    
    def __init__(
        self,
        base_url: str = "",
        backend: Literal["httpx", "aiohttp"] = "httpx",
        connect_timeout: float = 5.0,
        read_timeout: float = 30.0,
        write_timeout: float = 30.0,
        max_connections: int = 100,
        headers: Optional[Dict[str, str]] = None,
    ):
        self._base_url = base_url.rstrip("/") if base_url else ""
        self._backend = "aiohttp" if (backend == "aiohttp" and aiohttp) else "httpx"
        self._headers = headers or {}
        self._max_connections = max_connections
        self._connect_timeout = connect_timeout
        self._read_timeout = read_timeout
        self._write_timeout = write_timeout
        
        # httpx 客户端
        if self._backend == "httpx":
            timeout = httpx.Timeout(
                connect=connect_timeout,
                read=read_timeout,
                write=write_timeout,
                pool=connect_timeout,
            )
            limits = httpx.Limits(
                max_connections=max_connections,
                max_keepalive_connections=max_connections // 2,
            )
            client_kwargs = {
                "headers": self._headers,
                "timeout": timeout,
                "limits": limits,
            }
            if self._base_url:
                client_kwargs["base_url"] = self._base_url
            
            self._sync_client = httpx.Client(**client_kwargs)
            self._async_client = httpx.AsyncClient(**client_kwargs)
        else:
            self._sync_client = None
            self._async_client = None
        
        # aiohttp session（延迟初始化）
        self._aiohttp_session = None
        self._aiohttp_lock = asyncio.Lock()
    
    async def _get_aiohttp_session(self):
        if not self._aiohttp_session:
            async with self._aiohttp_lock:
                if not self._aiohttp_session:
                    base_url = self._base_url if self._base_url.startswith("http") else None
                    timeout = aiohttp.ClientTimeout(
                        total=None,
                        connect=self._connect_timeout,
                        sock_read=self._read_timeout,
                        sock_connect=self._connect_timeout,
                    )
                    connector = aiohttp.TCPConnector(
                        limit=self._max_connections,
                        ttl_dns_cache=300,
                    )
                    self._aiohttp_session = aiohttp.ClientSession(
                        base_url=base_url,
                        headers=self._headers,
                        timeout=timeout,
                        connector=connector,
                    )
        return self._aiohttp_session
    
    def _is_async_context(self) -> bool:
        try:
            asyncio.get_running_loop()
            return True
        except RuntimeError:
            return False
    
    # ============ 重试逻辑 ============
    
    def _retry_sync(self, func, method: str, cfg: RetryConfig):
        last_err = None
        for attempt in range(cfg.total):
            try:
                resp = func()
                if resp.status_code in cfg.status_forcelist:
                    raise httpx.HTTPStatusError(f"Status {resp.status_code}", request=None, response=resp)
                return resp
            except RETRYABLE_EXCEPTIONS as e:
                last_err = e
                if attempt + 1 >= cfg.total or method.upper() not in cfg.allowed_methods:
                    raise
                delay = cfg.backoff_factor * (2 ** attempt) + random.uniform(0, 0.05)
                time.sleep(delay)
        raise last_err
    
    async def _retry_async(self, func, method: str, cfg: RetryConfig):
        last_err = None
        for attempt in range(cfg.total):
            try:
                resp = await func()
                status = getattr(resp, "status_code", getattr(resp, "status", None))
                if status in cfg.status_forcelist:
                    raise httpx.HTTPStatusError(f"Status {status}", request=None, response=resp)
                return resp
            except RETRYABLE_EXCEPTIONS as e:
                last_err = e
                if attempt + 1 >= cfg.total or method.upper() not in cfg.allowed_methods:
                    raise
                delay = cfg.backoff_factor * (2 ** attempt) + random.uniform(0, 0.05)
                await asyncio.sleep(delay)
        raise last_err
    
    # ============ 核心请求方法 ============
    
    def _request_sync(self, method: str, url: str, retry: Optional[RetryConfig] = None, **kwargs) -> SmartResponse:
        if self._backend != "httpx":
            raise RuntimeError("Sync requests only supported with httpx backend")
        
        def _do():
            resp = self._sync_client.request(method, url, **kwargs)
            resp.raise_for_status()
            return resp
        
        try:
            if retry:
                resp = self._retry_sync(_do, method, retry)
            else:
                resp = _do()
            return SmartResponse(resp, "httpx")
        except httpx.HTTPStatusError as e:
            raise RequestFailed(
                f"Request failed with status {e.response.status_code}",
                status_code=e.response.status_code,
                original_error=e
            )
        except RETRYABLE_EXCEPTIONS as e:
            raise NetworkError(f"Network error: {str(e)}", original_error=e)
    
    async def _request_async(self, method: str, url: str, retry: Optional[RetryConfig] = None, **kwargs) -> SmartResponse:
        async def _do_httpx():
            resp = await self._async_client.request(method, url, **kwargs)
            resp.raise_for_status()
            return resp
        
        async def _do_aiohttp():
            session = await self._get_aiohttp_session()
            resp = await session.request(method, url, **kwargs)
            resp.raise_for_status()
            return resp
        
        try:
            if self._backend == "httpx":
                if retry:
                    resp = await self._retry_async(_do_httpx, method, retry)
                else:
                    resp = await _do_httpx()
                return SmartResponse(resp, "httpx")
            else:
                if retry:
                    resp = await self._retry_async(_do_aiohttp, method, retry)
                else:
                    resp = await _do_aiohttp()
                return SmartResponse(resp, "aiohttp")
        except httpx.HTTPStatusError as e:
            raise RequestFailed(
                f"Request failed with status {e.response.status_code}",
                status_code=e.response.status_code,
                original_error=e
            )
        except RETRYABLE_EXCEPTIONS as e:
            raise NetworkError(f"Network error: {str(e)}", original_error=e)
    
    def request(self, method: str, url: str, retry: Optional[RetryConfig] = None, **kwargs) -> Union[SmartResponse, "asyncio.coroutine"]:
        """
        发起请求。自动检测同步/异步环境。
        
        同步环境：直接返回 SmartResponse
        异步环境：返回 coroutine，需要 await
        """
        if self._is_async_context():
            return self._request_async(method, url, retry=retry, **kwargs)
        return self._request_sync(method, url, retry=retry, **kwargs)
    
    # ============ 快捷方法 ============
    
    def get(self, url: str, **kwargs):
        return self.request("GET", url, **kwargs)
    
    def post(self, url: str, **kwargs):
        return self.request("POST", url, **kwargs)
    
    def put(self, url: str, **kwargs):
        return self.request("PUT", url, **kwargs)
    
    def patch(self, url: str, **kwargs):
        return self.request("PATCH", url, **kwargs)
    
    def delete(self, url: str, **kwargs):
        return self.request("DELETE", url, **kwargs)
    
    def head(self, url: str, **kwargs):
        return self.request("HEAD", url, **kwargs)
    
    def options(self, url: str, **kwargs):
        return self.request("OPTIONS", url, **kwargs)
    
    # ============ 流式请求 ============
    
    def stream(self, method: str, url: str, **kwargs) -> DualModeStream:
        """
        流式请求。支持同步和异步两种模式。
        
        同步：with client.stream("POST", url) as resp: ...
        异步：async with client.stream("POST", url) as resp: ...
        """
        return DualModeStream(self, method, url, **kwargs)
    
    # ============ 生命周期管理 ============
    
    def close(self):
        if self._sync_client:
            self._sync_client.close()
        if self._async_client and not self._async_client.is_closed:
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(self._async_client.aclose())
            except RuntimeError:
                pass
    
    async def aclose(self):
        if self._sync_client:
            self._sync_client.close()
        if self._async_client:
            await self._async_client.aclose()
        if self._aiohttp_session:
            await self._aiohttp_session.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        self.close()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, *args):
        await self.aclose()