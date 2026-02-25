"""
Channels App HTTP API Client.

Async client for communicating with the Channels app HTTP API.
Replicates the pychannels interface using aiohttp for native async support.

API reference: https://getchannels.com/api/

:license: Mozilla Public License Version 2.0, see LICENSE for more details.
"""

import logging
from typing import Any

import aiohttp

_LOG = logging.getLogger(__name__)

DEFAULT_PORT = 57000
REQUEST_TIMEOUT = aiohttp.ClientTimeout(total=5)


class ChannelsClient:
    """Async HTTP client for the Channels app API."""

    def __init__(self, host: str, port: int = DEFAULT_PORT) -> None:
        self.host = host
        self.port = port

    @property
    def _base_url(self) -> str:
        return f"http://{self.host}:{self.port}"

    async def _request(
        self, method: str, path: str, params: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Make an HTTP request and return the parsed JSON response."""
        url = self._base_url + path
        try:
            async with aiohttp.ClientSession(timeout=REQUEST_TIMEOUT) as session:
                if method == "GET":
                    async with session.get(url) as response:
                        return await response.json(content_type=None)
                elif method == "POST":
                    async with session.post(url, json=params) as response:
                        return await response.json(content_type=None)
                elif method == "PUT":
                    async with session.put(url, json=params) as response:
                        return await response.json(content_type=None)
                elif method == "DELETE":
                    async with session.delete(url) as response:
                        return await response.json(content_type=None)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")
        except aiohttp.ClientResponseError:
            return {"status": "error"}
        except TimeoutError:
            return {"status": "offline"}
        except aiohttp.ClientError:
            return {"status": "offline"}

    async def _command(self, named_command: str) -> dict[str, Any]:
        """Send a named control command."""
        return await self._request("POST", f"/api/{named_command}")

    # --- Status ---

    async def status(self) -> dict[str, Any]:
        """Return the current playback state."""
        return await self._request("GET", "/api/status")

    async def favorite_channels(self) -> list[dict[str, Any]]:
        """Return the list of favorite channels."""
        response = await self._request("GET", "/api/favorite_channels")
        return response if isinstance(response, list) else []

    # --- Playback control ---

    async def toggle_pause(self) -> dict[str, Any]:
        """Toggle paused state."""
        return await self._command("toggle_pause")

    async def pause(self) -> dict[str, Any]:
        """Pause playback."""
        return await self._command("pause")

    async def resume(self) -> dict[str, Any]:
        """Resume playback."""
        return await self._command("resume")

    async def stop(self) -> dict[str, Any]:
        """Stop playback."""
        return await self._command("stop")

    async def seek(self, seconds: int) -> dict[str, Any]:
        """Seek by a relative number of seconds (positive or negative)."""
        return await self._command(f"seek/{seconds or 0}")

    async def seek_forward(self) -> dict[str, Any]:
        """Seek forward."""
        return await self._command("seek_forward")

    async def seek_backward(self) -> dict[str, Any]:
        """Seek backward."""
        return await self._command("seek_backward")

    async def skip_forward(self) -> dict[str, Any]:
        """Skip forward to the next chapter mark."""
        return await self._command("skip_forward")

    async def skip_backward(self) -> dict[str, Any]:
        """Skip backward to the previous chapter mark."""
        return await self._command("skip_backward")

    # --- Audio ---

    async def toggle_mute(self) -> dict[str, Any]:
        """Toggle mute state."""
        return await self._command("toggle_mute")

    async def toggle_pip(self) -> dict[str, Any]:
        """Toggle Picture in Picture."""
        return await self._command("toggle_pip")

    # --- Channels ---

    async def channel_up(self) -> dict[str, Any]:
        """Change to the next channel."""
        return await self._command("channel_up")

    async def channel_down(self) -> dict[str, Any]:
        """Change to the previous channel."""
        return await self._command("channel_down")

    async def previous_channel(self) -> dict[str, Any]:
        """Jump back to the last channel."""
        return await self._command("previous_channel")

    async def play_channel(self, channel_number: int | str) -> dict[str, Any]:
        """Tune to a specific channel number."""
        return await self._command(f"play/channel/{channel_number}")

    async def play_recording(self, recording_id: int | str) -> dict[str, Any]:
        """Play a specific recording by ID."""
        return await self._command(f"play/recording/{recording_id}")

    # --- UI ---

    async def navigate(self, section: str) -> dict[str, Any]:
        """Navigate to a named section of the app."""
        return await self._command(f"navigate/{section}")

    async def notify(self, title: str, message: str) -> dict[str, Any]:
        """Display an in-app notification."""
        return await self._request(
            "POST", "/api/notify", {"title": title, "message": message}
        )

    # --- Captions / Recording ---

    async def toggle_cc(self) -> dict[str, Any]:
        """Toggle closed captions."""
        return await self._command("toggle_cc")

    async def toggle_record(self) -> dict[str, Any]:
        """Toggle recording of the current program."""
        return await self._command("toggle_record")
