"""
SmartHTTP 完整测试套件
覆盖所有场景：httpx/aiohttp backend、sync/async、stream/non-stream、GET/POST
"""
import asyncio
import threading
import time
import pytest
import httpx
import uvicorn
from fastapi import FastAPI
from fastapi.responses import StreamingResponse, JSONResponse

from xhttpy.core import SmartHTTP, RetryConfig, SmartHTTPError, NetworkError




# ============ FastAPI 测试服务器 ============

app = FastAPI()
N = 3  # 流式响应的 chunk 数量


async def fake_data_streamer():
    for i in range(N):
        yield f"chunk {i}\n"
        await asyncio.sleep(0.05)


@app.get("/get")
async def get_endpoint():
    return {"method": "GET", "message": "hello"}


@app.post("/post")
async def post_endpoint():
    return {"method": "POST", "message": "world"}


@app.put("/put")
async def put_endpoint():
    return {"method": "PUT"}


@app.delete("/delete")
async def delete_endpoint():
    return {"method": "DELETE"}


@app.post("/stream")
async def stream_post_endpoint():
    return StreamingResponse(fake_data_streamer(), media_type="text/plain")


@app.get("/stream-get")
async def stream_get_endpoint():
    return StreamingResponse(fake_data_streamer(), media_type="text/plain")


@app.get("/status/{code}")
async def status_endpoint(code: int):
    return JSONResponse({"status": code}, status_code=code)


@pytest.fixture(scope="module")
def server():
    config = uvicorn.Config(app, host="127.0.0.1", port=18765, log_level="error")
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run)
    thread.start()
    time.sleep(1)  # 等待启动
    yield "http://127.0.0.1:18765"
    server.should_exit = True
    thread.join()


# ============================================================
# HTTPX Backend - 同步测试（使用 base_url）
# ============================================================

class TestHttpxSync:
    """httpx 后端 + 同步调用（使用 base_url + 相对路径）"""
    
    def test_get(self, server):
        # 使用 base_url，请求时只写相对路径
        with SmartHTTP(base_url=server, backend="httpx") as client:
            resp = client.get("/get")  # 自动拼接为 {server}/get
            assert resp.status_code == 200
            assert resp.json()["method"] == "GET"
    
    def test_post(self, server):
        with SmartHTTP(base_url=server, backend="httpx") as client:
            resp = client.post("/post", json={"key": "value"})
            assert resp.status_code == 200
            assert resp.json()["method"] == "POST"
    
    def test_put(self, server):
        with SmartHTTP(base_url=server, backend="httpx") as client:
            resp = client.put("/put", json={"key": "value"})
            assert resp.status_code == 200
            assert resp.json()["method"] == "PUT"
    
    def test_delete(self, server):
        with SmartHTTP(base_url=server, backend="httpx") as client:
            resp = client.delete("/delete")
            assert resp.status_code == 200
            assert resp.json()["method"] == "DELETE"
    
    def test_stream_get(self, server):
        with SmartHTTP(base_url=server, backend="httpx") as client:
            with client.stream("GET", "/stream-get") as resp:
                assert resp.status_code == 200
                chunks = list(resp.iter_lines())
                assert len(chunks) == N
                assert all("chunk" in c for c in chunks)
    
    def test_stream_post(self, server):
        with SmartHTTP(base_url=server, backend="httpx") as client:
            with client.stream("POST", "/stream") as resp:
                assert resp.status_code == 200
                chunks = list(resp.iter_lines())
                assert len(chunks) == N

    
    def test_stream_iter_bytes(self, server):
        with SmartHTTP(backend="httpx") as client:
            with client.stream("GET", f"{server}/stream-get") as resp:
                chunks = list(resp.iter_bytes(chunk_size=10))
                assert len(chunks) > 0


# ============================================================
# HTTPX Backend - 异步测试（使用 base_url）
# ============================================================

class TestHttpxAsync:
    """httpx 后端 + 异步调用（使用 base_url + 相对路径）"""
    
    @pytest.mark.asyncio
    async def test_get(self, server):
        # 使用 base_url，请求时只写相对路径
        async with SmartHTTP(base_url=server, backend="httpx") as client:
            resp = await client.get("/get")
            assert resp.status_code == 200
            data = await resp.json_async()
            assert data["method"] == "GET"
    
    @pytest.mark.asyncio
    async def test_post(self, server):
        async with SmartHTTP(base_url=server, backend="httpx") as client:
            resp = await client.post("/post", json={"key": "value"})
            assert resp.status_code == 200
            data = await resp.json_async()
            assert data["method"] == "POST"
    
    @pytest.mark.asyncio
    async def test_put(self, server):
        async with SmartHTTP(base_url=server, backend="httpx") as client:
            resp = await client.put("/put", json={"key": "value"})
            assert resp.status_code == 200
    
    @pytest.mark.asyncio
    async def test_delete(self, server):
        async with SmartHTTP(base_url=server, backend="httpx") as client:
            resp = await client.delete("/delete")
            assert resp.status_code == 200
    
    @pytest.mark.asyncio
    async def test_stream_get(self, server):
        async with SmartHTTP(base_url=server, backend="httpx") as client:
            async with client.stream("GET", "/stream-get") as resp:
                assert resp.status_code == 200
                chunks = []
                async for line in resp.iter_lines():
                    chunks.append(line)
                assert len(chunks) == N
    
    @pytest.mark.asyncio
    async def test_stream_post(self, server):
        async with SmartHTTP(base_url=server, backend="httpx") as client:
            async with client.stream("POST", "/stream") as resp:
                assert resp.status_code == 200
                chunks = []
                async for line in resp.iter_lines():
                    chunks.append(line)
                assert len(chunks) == N
    
    @pytest.mark.asyncio
    async def test_stream_iter_bytes(self, server):
        async with SmartHTTP(base_url=server, backend="httpx") as client:
            async with client.stream("GET", "/stream-get") as resp:
                chunks = []
                async for chunk in resp.iter_bytes(chunk_size=10):
                    chunks.append(chunk)
                assert len(chunks) > 0



# ============================================================
# AIOHTTP Backend - 异步测试
# ============================================================

class TestAiohttpAsync:
    """aiohttp 后端 + 异步调用"""
    
    @pytest.mark.asyncio
    async def test_get(self, server):
        async with SmartHTTP(backend="aiohttp") as client:
            resp = await client.get(f"{server}/get")
            assert resp.status_code == 200
            data = await resp.json_async()
            assert data["method"] == "GET"
    
    @pytest.mark.asyncio
    async def test_post(self, server):
        async with SmartHTTP(backend="aiohttp") as client:
            resp = await client.post(f"{server}/post", json={"key": "value"})
            assert resp.status_code == 200
            data = await resp.json_async()
            assert data["method"] == "POST"
    
    @pytest.mark.asyncio
    async def test_text_async(self, server):
        async with SmartHTTP(backend="aiohttp") as client:
            resp = await client.get(f"{server}/get")
            text = await resp.text_async()
            assert "GET" in text
    
    @pytest.mark.asyncio
    async def test_stream_get(self, server):
        async with SmartHTTP(backend="aiohttp") as client:
            async with client.stream("GET", f"{server}/stream-get") as resp:
                assert resp.status_code == 200
                chunks = []
                async for line in resp.iter_lines():
                    chunks.append(line)
                assert len(chunks) >= 1  # aiohttp 可能合并 chunks
    
    @pytest.mark.asyncio
    async def test_stream_post(self, server):
        async with SmartHTTP(backend="aiohttp") as client:
            async with client.stream("POST", f"{server}/stream") as resp:
                assert resp.status_code == 200
                chunks = []
                async for line in resp.iter_lines():
                    chunks.append(line)
                assert len(chunks) >= 1


# ============================================================
# 并发测试
# ============================================================

class TestConcurrency:
    """并发请求测试"""
    
    @pytest.mark.asyncio
    async def test_httpx_concurrent(self, server):
        async with SmartHTTP(backend="httpx") as client:
            async def one_call(i):
                resp = await client.get(f"{server}/get")
                return resp.status_code
            
            results = await asyncio.gather(*(one_call(i) for i in range(20)))
            assert all(r == 200 for r in results)
    
    @pytest.mark.asyncio
    async def test_aiohttp_concurrent(self, server):
        async with SmartHTTP(backend="aiohttp") as client:
            async def one_call(i):
                resp = await client.get(f"{server}/get")
                return resp.status_code
            
            results = await asyncio.gather(*(one_call(i) for i in range(20)))
            assert all(r == 200 for r in results)


# ============================================================
# 响应对象测试
# ============================================================

class TestSmartResponse:
    """SmartResponse 测试"""
    
    def test_sync_properties(self, server):
        with SmartHTTP() as client:
            resp = client.get(f"{server}/get")
            
            # status_code
            assert resp.status_code == 200
            
            # headers
            assert "content-type" in resp.headers
            
            # text
            assert "GET" in resp.text
            
            # json
            data = resp.json()
            assert isinstance(data, dict)
    
    @pytest.mark.asyncio
    async def test_async_properties(self, server):
        async with SmartHTTP() as client:
            resp = await client.get(f"{server}/get")
            
            # text_async
            text = await resp.text_async()
            assert "GET" in text
            
            # json_async
            data = await resp.json_async()
            assert data["method"] == "GET"


# ============================================================
# 客户端配置测试
# ============================================================

class TestClientConfig:
    """客户端配置测试"""
    
    def test_base_url(self, server):
        with SmartHTTP(base_url=server) as client:
            resp = client.get("/get")
            assert resp.status_code == 200
    
    def test_headers(self, server):
        with SmartHTTP(headers={"X-Custom": "test"}) as client:
            resp = client.get(f"{server}/get")
            assert resp.status_code == 200
    
    def test_timeout_config(self):
        client = SmartHTTP(
            connect_timeout=1.0,
            read_timeout=5.0,
            write_timeout=5.0,
        )
        assert client._connect_timeout == 1.0
        assert client._read_timeout == 5.0
        assert client._write_timeout == 5.0
        client.close()
    
    def test_max_connections(self):
        client = SmartHTTP(max_connections=50)
        assert client._max_connections == 50
        client.close()


# ============================================================
# 重试配置测试
# ============================================================

class TestRetryConfig:
    """重试配置测试"""
    
    def test_retry_config_defaults(self):
        cfg = RetryConfig()
        assert cfg.total == 3
        assert 500 in cfg.status_forcelist
        assert "GET" in cfg.allowed_methods
    
    def test_retry_config_custom(self):
        cfg = RetryConfig(total=5, backoff_factor=0.5)
        assert cfg.total == 5
        assert cfg.backoff_factor == 0.5


# ============================================================
# 错误处理测试
# ============================================================

class TestErrorHandling:
    """错误处理测试"""
    
    def test_http_error_sync(self, server):
        with SmartHTTP() as client:
            with pytest.raises(SmartHTTPError):
                client.get(f"{server}/status/500")
    
    @pytest.mark.asyncio
    async def test_http_error_async(self, server):
        async with SmartHTTP() as client:
            with pytest.raises(SmartHTTPError):
                await client.get(f"{server}/status/500")
