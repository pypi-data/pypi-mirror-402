"""GoXLR Utility API: Websocket Client"""

from __future__ import annotations

import asyncio
import socket
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any, Optional

import aiohttp

from .base import Base
from .const import (
    ACCENT,
    COMMAND_TYPE_LOAD_PROFILE,
    COMMAND_TYPE_LOAD_PROFILE_COLOURS,
    COMMAND_TYPE_SET_BUTTON_COLOURS,
    COMMAND_TYPE_SET_FADER_COLOURS,
    COMMAND_TYPE_SET_MUTE_STATE,
    COMMAND_TYPE_SET_SIMPLE_COLOUR,
    COMMAND_TYPE_SET_VOLUME,
    DEFAULT_HOST,
    DEFAULT_PORT,
    KEY_ID,
    KEY_TYPE,
    MUTED_STATE,
    REQUEST_TYPE_GET_STATUS,
    RESPONSE_TYPE_OK,
    RESPONSE_TYPE_PATCH,
    RESPONSE_TYPE_STATUS,
    UNMUTED_STATE,
)
from .exceptions import (
    BadMessageException,
    ConnectionClosedException,
    ConnectionErrorException,
)
from .models.patch import Patch
from .models.request import Request
from .models.response import Response
from .models.status import Status


@dataclass
class WebSocketClient:
    """GoXLR Utility API: WebSocket Client Model"""

    url: str
    headers: dict[str, str]
    timeout: int = 30
    reconnect_interval: int = 5
    max_retries: int = 3
    metadata: Optional[dict[str, Any]] = None


class WebsocketClient(Base):
    """Websocket Client"""

    def __init__(self) -> None:
        """Initialize."""
        super().__init__()
        self._session: Optional[aiohttp.ClientSession] = None
        self._websocket: Optional[aiohttp.ClientWebSocketResponse] = None
        self._message_id: int = 0
        self._message_queue: asyncio.Queue[dict] = asyncio.Queue()
        self._message_events: dict[int, asyncio.Event] = {}
        self._message_responses: dict[int, Response[Any]] = {}

    @property
    def connected(self) -> bool:
        """Return if we are connected."""
        return self._websocket is not None and not self._websocket.closed

    async def disconnect(self) -> None:
        """Disconnect."""
        if self._websocket is not None:
            await self._websocket.close()
            self._websocket = None
        if self._session is not None:
            await self._session.close()
            self._session = None

    async def connect(
        self,
        host: str = DEFAULT_HOST,
        port: int = DEFAULT_PORT,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> None:
        """Connect."""
        if self.connected:
            return

        if session is None:
            self._session = aiohttp.ClientSession()
        else:
            self._session = session

        try:
            self._websocket = await self._session.ws_connect(
                f"ws://{host}:{port}/api/websocket"
            )
        except (aiohttp.ClientError, socket.gaierror) as error:
            raise ConnectionErrorException from error

    async def _send_message(
        self,
        request: Request,
        wait_for_response: bool = True,
        response_type: Optional[str] = None,
    ) -> Response[Any]:
        """Send a message."""
        if not self.connected:
            raise ConnectionClosedException

        self._message_id += 1
        request.id = self._message_id

        if wait_for_response:
            self._message_events[request.id] = asyncio.Event()

        await self._websocket.send_json(request.__dict__)

        if not wait_for_response:
            return Response(id=request.id, type=RESPONSE_TYPE_OK, data=None)  # pylint: disable=unexpected-keyword-arg

        try:
            await self._message_events[request.id].wait()
        except asyncio.TimeoutError as error:
            raise ConnectionErrorException from error

        response = self._message_responses.pop(request.id)
        self._message_events.pop(request.id)

        if response_type is not None and response.type != response_type:
            raise BadMessageException(f"Expected {response_type}, got {response.type}")

        return response

    async def get_status(self) -> Status:
        """Get status."""
        response = await self._send_message(
            Request(id=None, data=REQUEST_TYPE_GET_STATUS),  # pylint: disable=unexpected-keyword-arg
            response_type=RESPONSE_TYPE_STATUS,
        )
        return response.data

    async def set_accent_color(
        self,
        color: str,
    ) -> None:
        """Set accent color."""
        await self._send_message(
            Request(  # pylint: disable=unexpected-keyword-arg
                id=None,
                data={
                    KEY_TYPE: COMMAND_TYPE_SET_SIMPLE_COLOUR,
                    ACCENT: color,
                },
            ),
            response_type=RESPONSE_TYPE_OK,
        )

    async def set_button_color(
        self,
        name: str,
        color_one: str,
        color_two: str,
    ) -> None:
        """Set button color."""
        await self._send_message(
            Request(  # pylint: disable=unexpected-keyword-arg
                id=None,
                data={
                    KEY_TYPE: COMMAND_TYPE_SET_BUTTON_COLOURS,
                    name: {
                        "colour_one": color_one,
                        "colour_two": color_two,
                    },
                },
            ),
            response_type=RESPONSE_TYPE_OK,
        )

    async def set_fader_color(
        self,
        name: str,
        color_top: str,
        color_bottom: str,
    ) -> None:
        """Set fader color."""
        await self._send_message(
            Request(  # pylint: disable=unexpected-keyword-arg
                id=None,
                data={
                    KEY_TYPE: COMMAND_TYPE_SET_FADER_COLOURS,
                    name: {
                        "colour_one": color_top,
                        "colour_two": color_bottom,
                    },
                },
            ),
            response_type=RESPONSE_TYPE_OK,
        )

    async def set_muted(
        self,
        channel: str,
        muted: bool,
    ) -> None:
        """Set muted."""
        await self._send_message(
            Request(  # pylint: disable=unexpected-keyword-arg
                id=None,
                data={
                    KEY_TYPE: COMMAND_TYPE_SET_MUTE_STATE,
                    channel: MUTED_STATE if muted else UNMUTED_STATE,
                },
            ),
            response_type=RESPONSE_TYPE_OK,
        )

    async def set_volume(
        self,
        channel: str,
        volume: int,
    ) -> None:
        """Set volume."""
        await self._send_message(
            Request(  # pylint: disable=unexpected-keyword-arg
                id=None,
                data={
                    KEY_TYPE: COMMAND_TYPE_SET_VOLUME,
                    channel: volume,
                },
            ),
            response_type=RESPONSE_TYPE_OK,
        )

    async def load_profile(
        self,
        profile: str,
    ) -> None:
        """Load profile."""
        await self._send_message(
            Request(  # pylint: disable=unexpected-keyword-arg
                id=None,
                data={
                    KEY_TYPE: COMMAND_TYPE_LOAD_PROFILE,
                    "profile": profile,
                },
            ),
            response_type=RESPONSE_TYPE_OK,
        )

    async def load_profile_colours(
        self,
        profile: str,
    ) -> None:
        """Load profile colours."""
        await self._send_message(
            Request(  # pylint: disable=unexpected-keyword-arg
                id=None,
                data={
                    KEY_TYPE: COMMAND_TYPE_LOAD_PROFILE_COLOURS,
                    "profile": profile,
                },
            ),
            response_type=RESPONSE_TYPE_OK,
        )

    async def listen(
        self,
        patch_callback: Optional[Callable[[Response[Patch]], Awaitable[None]]] = None,
    ) -> None:
        """Listen for messages."""

        async def _message_callback(message: dict) -> None:
            """Handle message."""
            try:
                if KEY_ID in message:
                    response = Response(**message)
                    if response.id in self._message_events:
                        self._message_responses[response.id] = response
                        self._message_events[response.id].set()
                    return

                if KEY_TYPE in message and message[KEY_TYPE] == RESPONSE_TYPE_PATCH:
                    response = Response(**message)
                    if patch_callback is not None:
                        await patch_callback(response)
                    return

                if KEY_TYPE in message and message[KEY_TYPE] == RESPONSE_TYPE_STATUS:
                    response = Response(**message)
                    if patch_callback is not None:
                        await patch_callback(response)
                    return
            except (TypeError, ValueError) as error:
                raise BadMessageException from error

        await self._listen_for_messages(_message_callback)

    async def _listen_for_messages(
        self,
        callback: Callable[[dict[Any, Any]], Awaitable[None]],
    ) -> None:
        """Listen for messages."""
        if not self.connected:
            raise ConnectionClosedException

        while True:
            try:
                if (message := await self.receive_message()) is None:
                    break
                await callback(message)
            except (TypeError, ValueError) as error:
                raise BadMessageException from error

    async def receive_message(self) -> Optional[dict]:
        """Receive message."""
        if not self.connected:
            raise ConnectionClosedException

        try:
            message = await self._websocket.receive_json()
            return message
        except (aiohttp.ClientError, TypeError) as error:
            raise ConnectionErrorException from error
