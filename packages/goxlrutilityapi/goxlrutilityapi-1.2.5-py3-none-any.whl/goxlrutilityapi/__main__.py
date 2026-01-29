"""GoXLR Utility API: Main"""
from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import Optional

import typer

from ._version import __version__
from .const import KEY_DATA, KEY_ID, KEY_TYPE
from .exceptions import (
    BadMessageException,
    ConnectionClosedException,
    ConnectionErrorException,
)
from .logger import setup_logger
from .models.patch import Patch
from .models.response import Response
from .models.status import Status
from .websocket_client import WebsocketClient

app = typer.Typer()

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
websocket_client = WebsocketClient()


def setup_websocket(
    callback: Optional[Callable[[Response[Patch]], Awaitable[None]]] = None
) -> bool:
    """Listen for messages in the background"""
    try:
        loop.run_until_complete(websocket_client.connect())
        loop.create_task(
            websocket_client.listen(callback),
            name="Websocket Listener",
        )
    except (
        BadMessageException,
        ConnectionClosedException,
        ConnectionErrorException,
    ) as error:
        typer.secho(f"Error: {error}", fg=typer.colors.RED)
        loop.stop()
        return False
    return True


async def patch_callback(response: Response[Patch]) -> None:
    """Patch response callback function"""
    typer.secho(
        response.json(
            include={
                KEY_ID,
                KEY_TYPE,
                KEY_DATA,
            },
            exclude_unset=True,
        ),
        fg=typer.colors.GREEN,
    )


@app.command(name="get_status", short_help="Get Status of GoXLR")
def get_status(debug: bool = False) -> None:
    """Get Status of GoXLR"""
    if debug:
        setup_logger("DEBUG")
    if setup_websocket() is False:
        typer.secho("Failed to connect to GoXLR", fg=typer.colors.RED)
        return
    try:
        status: Status = loop.run_until_complete(websocket_client.get_status())
    except BadMessageException as error:
        typer.secho(
            f"Failed to get status from GoXLR: {error}",
            fg=typer.colors.RED,
        )
        return

    typer.secho(status.json(), fg=typer.colors.GREEN)


@app.command(
    name="listen_for_messages",
    short_help="Listen for patch messages from GoXLR",
)
def listen_for_messages(debug: bool = False) -> None:
    """Listen for patch messages from GoXLR"""
    if debug:
        setup_logger("DEBUG")
    setup_websocket(patch_callback)
    typer.secho("Listening for messages...", fg=typer.colors.GREEN)
    loop.run_forever()


@app.command(name="set_accent_color", short_help="Set Accent Color")
def set_accent_color(
    color: str = typer.Argument(..., help="Color Hex Value (RRGGBB)"),
    debug: bool = False,
) -> None:
    """Set Accent Color"""
    if debug:
        setup_logger("DEBUG")
    if setup_websocket() is False:
        typer.secho("Failed to connect to GoXLR", fg=typer.colors.RED)
        return
    try:
        loop.run_until_complete(websocket_client.get_status())
    except BadMessageException as error:
        typer.secho(
            f"Failed to get status from GoXLR: {error}",
            fg=typer.colors.RED,
        )
        return

    try:
        loop.run_until_complete(websocket_client.set_accent_color(color))
    except BadMessageException as error:
        typer.secho(
            f"Failed to set accent color: {error}",
            fg=typer.colors.RED,
        )
        return

    typer.secho(f"Accent color set to {color}", fg=typer.colors.GREEN)


@app.command(name="set_fader_color", short_help="Set Fader Color")
def set_fader_color(
    fader: str = typer.Argument(..., help="Fader Name"),
    color_top: str = typer.Argument(..., help="Color 1 Hex Value (RRGGBB)"),
    color_bottom: str = typer.Argument(..., help="Color 2 Hex Value (RRGGBB)"),
    debug: bool = False,
) -> None:
    """Set Fader Color"""
    if debug:
        setup_logger("DEBUG")
    if setup_websocket() is False:
        typer.secho("Failed to connect to GoXLR", fg=typer.colors.RED)
        return
    try:
        loop.run_until_complete(websocket_client.get_status())
    except BadMessageException as error:
        typer.secho(
            f"Failed to get status from GoXLR: {error}",
            fg=typer.colors.RED,
        )
        return

    try:
        loop.run_until_complete(
            websocket_client.set_fader_color(
                fader,
                color_top,
                color_bottom,
            )
        )
    except BadMessageException as error:
        typer.secho(
            f"Failed to set fader color: {error}",
            fg=typer.colors.RED,
        )
        return

    typer.secho(
        f"Fader {fader} color set to {color_top} and {color_bottom}",
        fg=typer.colors.GREEN,
    )


@app.command(name="set_button_color", short_help="Set Button Color")
def set_button_color(
    button: str = typer.Argument(..., help="Button Name"),
    color_one: str = typer.Argument(..., help="Color 1 Hex Value (RRGGBB)"),
    color_two: str = typer.Argument(..., help="Color 2 Hex Value (RRGGBB)"),
    debug: bool = False,
) -> None:
    """Set Button Color"""
    if debug:
        setup_logger("DEBUG")
    if setup_websocket() is False:
        typer.secho("Failed to connect to GoXLR", fg=typer.colors.RED)
        return
    try:
        loop.run_until_complete(websocket_client.get_status())
    except BadMessageException as error:
        typer.secho(
            f"Failed to get status from GoXLR: {error}",
            fg=typer.colors.RED,
        )
        return

    try:
        loop.run_until_complete(
            websocket_client.set_button_color(
                button,
                color_one,
                color_two,
            )
        )
    except BadMessageException as error:
        typer.secho(
            f"Failed to set button color: {error}",
            fg=typer.colors.RED,
        )
        return

    typer.secho(
        f"{button} color set to {color_one} and {color_two}",
        fg=typer.colors.GREEN,
    )


@app.command(name="set_muted", short_help="Set Muted of Channel")
def set_muted(
    channel: str = typer.Argument(..., help="Channel Name"),
    muted: bool = typer.Argument(..., help="Muted (True/False)"),
    debug: bool = False,
) -> None:
    """Set Muted of Channel"""
    if debug:
        setup_logger("DEBUG")
    if setup_websocket() is False:
        typer.secho("Failed to connect to GoXLR", fg=typer.colors.RED)
        return
    try:
        loop.run_until_complete(websocket_client.get_status())
    except BadMessageException as error:
        typer.secho(
            f"Failed to get status from GoXLR: {error}",
            fg=typer.colors.RED,
        )
        return

    try:
        loop.run_until_complete(
            websocket_client.set_muted(
                channel,
                muted,
            )
        )
    except BadMessageException as error:
        typer.secho(
            f"Failed to set muted: {error}",
            fg=typer.colors.RED,
        )
        return

    typer.secho(
        f"{channel} muted set to {muted}",
        fg=typer.colors.GREEN,
    )


@app.command(name="set_volume", short_help="Set Volume of Channel")
def set_volume(
    channel: str = typer.Argument(..., help="Channel Name"),
    volume: int = typer.Argument(..., help="Volume (0-100)"),
    debug: bool = False,
) -> None:
    """Set Volume of Channel"""
    if debug:
        setup_logger("DEBUG")
    if setup_websocket() is False:
        typer.secho("Failed to connect to GoXLR", fg=typer.colors.RED)
        return
    try:
        loop.run_until_complete(websocket_client.get_status())
    except BadMessageException as error:
        typer.secho(
            f"Failed to get status from GoXLR: {error}",
            fg=typer.colors.RED,
        )
        return

    try:
        loop.run_until_complete(
            websocket_client.set_volume(
                channel,
                volume,
            )
        )
    except BadMessageException as error:
        typer.secho(
            f"Failed to set volume: {error}",
            fg=typer.colors.RED,
        )
        return

    typer.secho(
        f"{channel} volume set to {volume}",
        fg=typer.colors.GREEN,
    )


@app.command(name="load_profile", short_help="Load Profile")
def load_profile(
    profile: str = typer.Argument(..., help="Profile Name"),
    debug: bool = False,
) -> None:
    """Load Profile"""
    if debug:
        setup_logger("DEBUG")
    if setup_websocket() is False:
        typer.secho("Failed to connect to GoXLR", fg=typer.colors.RED)
        return
    try:
        loop.run_until_complete(websocket_client.get_status())
    except BadMessageException as error:
        typer.secho(
            f"Failed to get status from GoXLR: {error}",
            fg=typer.colors.RED,
        )
        return

    try:
        loop.run_until_complete(
            websocket_client.load_profile(
                profile,
            )
        )
    except BadMessageException as error:
        typer.secho(
            f"Failed to load profile: {error}",
            fg=typer.colors.RED,
        )
        return

    typer.secho(
        f"Profile {profile} loaded",
        fg=typer.colors.GREEN,
    )


@app.command(name="load_profile_colours", short_help="Load Profile Colours")
def load_profile_colours(
    profile: str = typer.Argument(..., help="Profile Name"),
    debug: bool = False,
) -> None:
    """Load Profile Colours"""
    if debug:
        setup_logger("DEBUG")
    if setup_websocket() is False:
        typer.secho("Failed to connect to GoXLR", fg=typer.colors.RED)
        return
    try:
        loop.run_until_complete(websocket_client.get_status())
    except BadMessageException as error:
        typer.secho(
            f"Failed to get status from GoXLR: {error}",
            fg=typer.colors.RED,
        )
        return

    try:
        loop.run_until_complete(
            websocket_client.load_profile_colours(
                profile,
            )
        )
    except BadMessageException as error:
        typer.secho(
            f"Failed to load profile colours: {error}",
            fg=typer.colors.RED,
        )
        return

    typer.secho(
        f"Profile colours {profile} loaded",
        fg=typer.colors.GREEN,
    )


@app.command(name="version", short_help="Module Version")
def version() -> None:
    """Module Version"""
    typer.secho(__version__.public(), fg=typer.colors.CYAN)


if __name__ == "__main__":
    app()
    loop.stop()
