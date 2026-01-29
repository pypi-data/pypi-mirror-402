"""WebSocket client for communicating with the clicker binary."""

import asyncio
import json
from typing import Any, Dict, Optional

from websockets.asyncio.client import ClientConnection, connect as ws_connect
from websockets.exceptions import ConnectionClosed


class BiDiError(Exception):
    """Raised when a BiDi command fails."""

    def __init__(self, error: str, message: str):
        self.error = error
        self.message = message
        super().__init__(f"{error}: {message}")


class BiDiClient:
    """WebSocket client for BiDi protocol."""

    def __init__(self, ws: ClientConnection):
        self._ws = ws
        self._next_id = 1
        self._pending: Dict[int, asyncio.Future] = {}
        self._receiver_task: Optional[asyncio.Task] = None

    @classmethod
    async def connect(cls, url: str) -> "BiDiClient":
        """Connect to a BiDi WebSocket server.

        Args:
            url: WebSocket URL (e.g., "ws://localhost:9515").

        Returns:
            A connected BiDiClient instance.
        """
        ws = await ws_connect(url)
        client = cls(ws)
        client._receiver_task = asyncio.create_task(client._receive_loop())
        return client

    async def _receive_loop(self) -> None:
        """Background task to receive and dispatch messages."""
        try:
            async for message in self._ws:
                data = json.loads(message)
                msg_id = data.get("id")
                if msg_id is not None and msg_id in self._pending:
                    self._pending[msg_id].set_result(data)
        except ConnectionClosed:
            # Connection closed, cancel all pending futures
            for future in self._pending.values():
                if not future.done():
                    future.set_exception(ConnectionError("Connection closed"))

    async def send(self, method: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """Send a command and wait for the response.

        Args:
            method: The BiDi method name (e.g., "browsingContext.navigate").
            params: Optional parameters for the command.

        Returns:
            The result from the response.

        Raises:
            BiDiError: If the command returns an error.
        """
        msg_id = self._next_id
        self._next_id += 1

        command = {
            "id": msg_id,
            "method": method,
            "params": params or {},
        }

        # Create future for response
        future: asyncio.Future = asyncio.get_event_loop().create_future()
        self._pending[msg_id] = future

        try:
            await self._ws.send(json.dumps(command))
            response = await future

            if response.get("type") == "error":
                raise BiDiError(
                    response.get("error", "unknown"),
                    response.get("message", "Unknown error"),
                )

            return response.get("result")
        finally:
            self._pending.pop(msg_id, None)

    async def close(self) -> None:
        """Close the WebSocket connection."""
        if self._receiver_task:
            self._receiver_task.cancel()
            try:
                await self._receiver_task
            except asyncio.CancelledError:
                pass

        await self._ws.close()
