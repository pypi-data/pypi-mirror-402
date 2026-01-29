import asyncio
import json
import threading
import time

from concurrent.futures import Future as ConcurrentFuture
from typing import Any, Optional, Coroutine, List, Dict

from mcp.client.session import ClientSession
from mcp.client.sse import sse_client

from xgae.engine.engine_base import  XGAToolResult


class AsyncToolExecutor:
    _instance = None
    _loop = None
    _thread = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._init_event_loop()
            return cls._instance


    @classmethod
    def _init_event_loop(cls):
        if cls._loop is None or cls._loop.is_closed():
            cls._loop = asyncio.new_event_loop()

        def start_loop(loop):
            asyncio.set_event_loop(loop)
            try:
                loop.run_forever()
            finally:
                if not loop.is_closed():
                    loop.close()

        cls._thread = threading.Thread(target=start_loop, args=(cls._loop,), daemon=True)
        cls._thread.start()

        time.sleep(0.1)

    @classmethod
    def submit(cls, coro: Coroutine) -> ConcurrentFuture:
        if cls._loop is None or cls._loop.is_closed():
            cls._init_event_loop()

        return asyncio.run_coroutine_threadsafe(coro, cls._loop)

    @classmethod
    def run_and_wait(cls, coro: Coroutine, timeout: Optional[float] = None) -> Any:
        future = cls.submit(coro)
        return future.result(timeout=timeout)

    @classmethod
    def get_loop(cls):
        if cls._loop is None or cls._loop.is_closed():
            cls._init_event_loop()
        return cls._loop

    @classmethod
    def shutdown(cls):
        if cls._loop is not None and not cls._loop.is_closed():
            cls._loop.call_soon_threadsafe(cls._loop.stop)

from mcp.types import CallToolResult

async def _mcp_sse_tool_call(url: str, tool_name: str, arguments: dict[str, Any]) -> CallToolResult:
    async with sse_client(url, sse_read_timeout=5) as streams:
        async with ClientSession(*streams) as session:
            await session.initialize()
            return  await session.call_tool(tool_name, arguments)


def call_mcp_tool(url: str, tool_name: str, arguments: dict[str, Any], timeout: Optional[float] = None) -> Any:
    future = AsyncToolExecutor.submit(_mcp_sse_tool_call(url, tool_name, arguments))
    mcp_result:CallToolResult =  future.result(timeout=timeout)
    result = {
        'isError': mcp_result.isError,
    }
    if mcp_result.isError:
        result['content'] = mcp_result.content[0].text
    else:
        result['content'] = mcp_result.structuredContent['result']

    return  json.dumps(result)


def convert_mcp_tool_result(org_result: str)->XGAToolResult:
    result = XGAToolResult(success=True, output=str(org_result))

    if org_result and isinstance(org_result, str) and "isError" in org_result:
        try:
            _result:dict = json.loads(org_result)
            content = _result.get('content', None)
            isError = _result.get('isError', None)

            if content and isError:
                success = not bool(isError)
                result = XGAToolResult(success=bool(success), output=str(content))
        except:
            pass

    return result


if __name__ == "__main__":
    async def sample_task(name, duration):
        print(f"Task '{name}' Begin，time = {duration} ")
        await asyncio.sleep(duration)
        return f"Task '{name}' Finished"

    async def main():
        try:
            # result = AsyncToolExecutor.run_and_wait(sample_task("mytool", 1))
            # print(f"Result1: {result}")

            result = call_mcp_tool("http://localhost:17070/sse", "get_alarm", {"ip":"13.0.0.13"})
            result = convert_mcp_tool_result(result)
            print(f"Result2: {result}")

            result = call_mcp_tool("http://localhost:17070/sse", "get_alarm1", {"ip":"13.0.0.13"})
            result = convert_mcp_tool_result(result)
            print(f"Result3: {result}")

        except Exception as e:
            print(f"Thread Fail: {e}")

    with asyncio.Runner() as runner:
            runner.run(main())