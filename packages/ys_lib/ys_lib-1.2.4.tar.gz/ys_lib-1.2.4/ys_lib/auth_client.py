# -*- coding: utf-8 -*-
import asyncio
import json
import random
from typing import Any, Callable, Dict, Optional

import websockets
from loguru import logger
from websockets import ClientConnection


class AuthClient:
    def __init__(
        self,
        uri: str,
        generator: Callable,
        connect_callback: Optional[Callable] = None,
        event_callback: Optional[Callable] = None,
    ):
        assert uri and generator
        self.uri: str = uri
        self.generator: Callable = generator
        self.connect_callback: Optional[Callable] = connect_callback
        self.event_callback: Optional[Callable] = event_callback
        self.app_id: str = ""
        # connect status
        self.ws: Optional[ClientConnection] = None
        self.connected: asyncio.Event = asyncio.Event()
        self._conn_id: int = 0
        self._req_seq: int = 0
        self._pending_futures: Dict[str, asyncio.Future] = {}
        self._connect_task: asyncio.Task = asyncio.create_task(self._connect_loop())

    @property
    def _next_request_id(self):
        self._req_seq += 1
        return f"{self._conn_id}_{self._req_seq}"

    async def _connect_loop(self):
        reconnect_delay: float = 1.0
        max_delay: float = 30.0
        while not self.connected.is_set():
            try:
                logger.debug("Connecting to AuthServer...")
                self.ws = await websockets.connect(  # type: ignore
                    uri=self.uri,
                    max_size=2**32 - 1,
                    max_queue=2**8,
                    write_limit=2**32 - 1,
                    ssl=None,
                )
                logger.success("Connected to AuthServer!")
                self.connected.set()
                reconnect_delay = 1.0
                asyncio.create_task(self._safe_callback(self.connect_callback, True))
                await self._recv_loop()
            except Exception as e:
                logger.error(f"[{e.__class__.__name__}]{e}")
            finally:
                await self.clear_connect_state()
                asyncio.create_task(self._safe_callback(self.connect_callback, False))
                # reconnect wait
                wait_time = reconnect_delay + random.uniform(0, 1)
                logger.warning(f"Reconnecting in {wait_time:.2f} seconds...")
                await asyncio.sleep(wait_time)
                reconnect_delay = min(reconnect_delay * 2, max_delay)
        self._connect_task.cancel()

    async def clear_connect_state(self):
        self.connected.clear()
        self.app_id = ""
        for fut in self._pending_futures.values():
            if not fut.done():
                fut.set_exception(ConnectionError("Connection closed"))
        self._pending_futures.clear()
        if self.ws:
            try:
                await self.ws.close()
            except Exception:
                pass
            self.ws = None
        logger.warning("Client closed.")

    async def _send_data(self, data: str):
        if self.ws and self.connected.is_set():
            # logger.info(f"Send:{data}")
            await self.ws.send(data)

    async def _recv_loop(self):
        while self.connected.is_set():
            message: str = await self.ws.recv()  # type: ignore
            # logger.info(f"Recv:{message[:100]}")
            try:
                payload = json.loads(message)
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON message: {message[:100]}")
                continue
            event = payload.get("event")
            if event == "push_connection_id":
                self._conn_id = payload.get("data", {}).get("connection_id")
                self._req_seq = 0
                asyncio.create_task(self._auto_set_app())
                asyncio.create_task(self._ping_loop())
                continue
            resp_id = payload.get("response_id") or payload.get("request_id")
            if resp_id and resp_id in self._pending_futures:
                future = self._pending_futures[resp_id]
                if not future.done():
                    future.set_result(payload)
                continue
            asyncio.create_task(self._safe_callback(self.event_callback, payload))
        logger.warning("Receive loop stopped.")

    async def login(self, info: dict) -> tuple[str, Any]:
        error, data = await self.call(event="login", data=info)
        return error, data

    async def logout_by_session_id(self, info: dict) -> tuple[str, Any]:
        error, data = await self.call(event="logout_by_session_id", data=info)
        return error, data

    async def call(
        self, event: str, data: Any = None, timeout: float = 10
    ) -> tuple[str, Any]:
        req_id = self._next_request_id
        payload = {"event": event, "request_id": req_id, "data": data}
        error: str = ""
        _data: Any = None
        try:
            future = asyncio.get_running_loop().create_future()
            self._pending_futures[req_id] = future
            await self._send_data(json.dumps(payload))
            resp = await asyncio.wait_for(future, timeout=timeout)
            if resp.get("code") != 0:
                error = resp.get("message") or "Unknown Error"
            _data = resp.get("data")
        except Exception as e:
            logger.error(f"[{e.__class__.__name__}]{e}")
            error = e.__class__.__name__
            if self.ws:
                try:
                    await self.ws.close(reason=str(e))
                except Exception:
                    pass
            self.connected.clear()
        finally:
            self._pending_futures.pop(req_id, None)
            return error, _data

    async def _auto_set_app(self):
        while not self.app_id and self.connected.is_set():
            try:
                error, data = await self.call(event="set_app", data=self.generator())
                assert not error and data, error
                self.app_id = data.get("app_id")
                logger.success(f"set app success, app_id={self.app_id}")
            except Exception as e:
                logger.error(f"set app failed,error={e}")
                await asyncio.sleep(1)

    async def _ping_loop(self, interval: float = 3.0):
        while self.connected.is_set():
            await asyncio.sleep(interval)
            await self.call(event="ping", timeout=3)

    @staticmethod
    async def _safe_callback(func, *args):
        try:
            await func(*args)
        except Exception as e:
            logger.error(f"Callback error: {e}")
