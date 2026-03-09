"""
Channels App Device Communication Module.

This module handles all communication with the Channels app via the async ChannelsClient.
It uses a PollingDevice to periodically query the Channels API for status updates.

:license: Mozilla Public License Version 2.0, see LICENSE for more details.
"""

import logging
import os
from asyncio import AbstractEventLoop
from typing import Any

from api import ChannelsClient
from const import DeviceConfig
from ucapi import media_player
from ucapi_framework import (
    BaseConfigManager,
    PollingDevice,
    BaseIntegrationDriver,
)
from ucapi_framework.helpers import MediaPlayerAttributes

_LOG = logging.getLogger(__name__)

# Default polling interval in seconds
POLL_INTERVAL = int(os.getenv("UC_CHANNELS_POLL_INTERVAL", "5"))

# Map Channels status strings to ucapi States
_CHANNELS_STATE_MAP = {
    "playing": media_player.States.PLAYING,
    "paused": media_player.States.PAUSED,
    "stopped": media_player.States.OFF,
    "error": media_player.States.UNKNOWN,
    "offline": media_player.States.UNAVAILABLE,
}


class Device(PollingDevice):
    """
    Device class for the Channels app.

    Uses the ChannelsClient to communicate with the Channels HTTP API.
    Polls the device every POLL_INTERVAL seconds to keep state up to date.
    State is stored in dicts keyed by device identifier and propagated to
    entities via push_update() / sync_state().
    """

    def __init__(
        self,
        device_config: DeviceConfig,
        loop: AbstractEventLoop | None = None,
        config_manager: BaseConfigManager | None = None,
        driver: BaseIntegrationDriver | None = None,
    ) -> None:
        super().__init__(
            device_config=device_config,
            loop=loop,
            poll_interval=POLL_INTERVAL,
            config_manager=config_manager,
            driver=driver,
        )

        self._client = ChannelsClient(
            host=device_config.address, port=device_config.port
        )

        self._media_player_attributes = MediaPlayerAttributes(
            STATE=None,
            MUTED=None,
            MEDIA_TYPE=None,
            MEDIA_TITLE=None,
            MEDIA_ARTIST=None,
            MEDIA_IMAGE_URL=None,
            MEDIA_POSITION=None,
            MEDIA_DURATION=None,
        )

    @property
    def identifier(self) -> str:
        return self._device_config.identifier

    @property
    def name(self) -> str:
        return self._device_config.name

    @property
    def address(self) -> str | None:
        return self._device_config.address

    @property
    def log_id(self) -> str:
        return self.name if self.name else self.identifier

    def get_media_player_attributes(self) -> MediaPlayerAttributes:
        """Return current media player attributes."""
        return self._media_player_attributes

    async def establish_connection(self) -> None:
        _LOG.debug(
            "[%s] Establishing connection to Channels at %s", self.log_id, self.address
        )
        status = await self._client.status()
        if status.get("status") == "offline":
            raise ConnectionError(
                f"Channels app at {self.address} is offline or unreachable"
            )
        self._update_state_from_status(status)
        self.push_update()
        _LOG.info(
            "[%s] Connected to Channels app, status: %s",
            self.log_id,
            status.get("status"),
        )

    async def poll_device(self) -> None:
        try:
            status = await self._client.status()
            if status.get("status") == "offline":
                _LOG.warning("[%s] Channels app is offline", self.log_id)
                self._media_player_attributes.STATE = media_player.States.UNAVAILABLE
            else:
                self._update_state_from_status(status)
        except Exception as err:  # pylint: disable=broad-exception-caught
            _LOG.error("[%s] Error polling Channels app: %s", self.log_id, err)
            self._media_player_attributes.STATE = media_player.States.UNAVAILABLE

        self.push_update()

    def _update_state_from_status(self, status: dict[str, Any]) -> None:
        attrs = self._media_player_attributes

        channels_status = status.get("status", "stopped")
        attrs.STATE = _CHANNELS_STATE_MAP.get(
            channels_status, media_player.States.UNKNOWN
        )
        attrs.MUTED = status.get("muted", False)

        playback_time = status.get("playback_time")
        attrs.MEDIA_POSITION = int(playback_time) if playback_time is not None else None

        now_playing = status.get("now_playing")
        channel = status.get("channel")

        if now_playing:
            content_type = now_playing.get("type", "")
            attrs.MEDIA_TYPE = (
                media_player.MediaType.VIDEO
                if content_type == "movie"
                else media_player.MediaType.TVSHOW
            )

            title = now_playing.get("title")
            episode_title = now_playing.get("episode_title")
            if title and episode_title:
                attrs.MEDIA_TITLE = f"{title} - {episode_title}"
            elif title:
                attrs.MEDIA_TITLE = title
            else:
                attrs.MEDIA_TITLE = None

            attrs.MEDIA_ARTIST = (
                channel.get("name") if channel and channel.get("name") else None
            )

            image_url = now_playing.get("image_url") or now_playing.get("thumb_url")
            if not image_url and channel:
                image_url = channel.get("image_url")
            attrs.MEDIA_IMAGE_URL = image_url

            duration = now_playing.get("duration")
            attrs.MEDIA_DURATION = int(duration) if duration is not None else None

        elif channel:
            attrs.MEDIA_TYPE = media_player.MediaType.TVSHOW
            attrs.MEDIA_TITLE = channel.get("name")
            attrs.MEDIA_ARTIST = "Ch. " + channel.get("number", "")
            attrs.MEDIA_IMAGE_URL = channel.get("image_url")
            attrs.MEDIA_DURATION = None
        else:
            attrs.MEDIA_TYPE = None
            attrs.MEDIA_TITLE = None
            attrs.MEDIA_ARTIST = None
            attrs.MEDIA_IMAGE_URL = None
            attrs.MEDIA_DURATION = None

    async def play_pause(self) -> None:
        _LOG.debug("[%s] Toggle play/pause", self.log_id)
        await self._client.toggle_pause()

    async def pause(self) -> None:
        _LOG.debug("[%s] Pause", self.log_id)
        await self._client.pause()

    async def play(self) -> None:
        _LOG.debug("[%s] Resume", self.log_id)
        await self._client.resume()

    async def stop(self) -> None:
        _LOG.debug("[%s] Stop", self.log_id)
        await self._client.stop()

    async def mute_toggle(self) -> None:
        _LOG.debug("[%s] Toggle mute", self.log_id)
        await self._client.toggle_mute()

    async def channel_up(self) -> None:
        _LOG.debug("[%s] Channel up", self.log_id)
        await self._client.channel_up()

    async def channel_down(self) -> None:
        _LOG.debug("[%s] Channel down", self.log_id)
        await self._client.channel_down()

    async def previous_channel(self) -> None:
        _LOG.debug("[%s] Previous channel", self.log_id)
        await self._client.previous_channel()

    async def seek_forward(self) -> None:
        _LOG.debug("[%s] Seek forward", self.log_id)
        await self._client.seek_forward()

    async def seek_backward(self) -> None:
        _LOG.debug("[%s] Seek backward", self.log_id)
        await self._client.seek_backward()

    async def skip_forward(self) -> None:
        _LOG.debug("[%s] Skip forward", self.log_id)
        await self._client.skip_forward()

    async def skip_backward(self) -> None:
        _LOG.debug("[%s] Skip backward", self.log_id)
        await self._client.skip_backward()

    async def seek(self, position: int) -> None:
        _LOG.debug("[%s] Seek to %s seconds", self.log_id, position)
        attrs = self._media_player_attributes
        current = attrs.MEDIA_POSITION or 0
        delta = position - current
        if delta != 0:
            await self._client.seek(delta)

    async def toggle_cc(self) -> None:
        _LOG.debug("[%s] Toggle closed captions", self.log_id)
        await self._client.toggle_cc()

    async def toggle_pip(self) -> None:
        _LOG.debug("[%s] Toggle picture in picture", self.log_id)
        await self._client.toggle_pip()

    async def toggle_record(self) -> None:
        _LOG.debug("[%s] Toggle record", self.log_id)
        await self._client.toggle_record()
