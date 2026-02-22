"""
Channels App Device Communication Module.

This module handles all communication with the Channels app via the async ChannelsClient.
It uses a PollingDevice to periodically query the Channels API for status updates.

:license: Mozilla Public License Version 2.0, see LICENSE for more details.
"""

import logging
from asyncio import AbstractEventLoop
from typing import Any

from api import ChannelsClient
from const import DeviceConfig
from ucapi import media_player
from ucapi import EntityTypes
from ucapi_framework import (
    BaseConfigManager,
    PollingDevice,
    BaseIntegrationDriver,
    DeviceEvents,
    EntitySource,
)
from ucapi_framework.entity import Entity as FrameworkEntity
from ucapi_framework.helpers import MediaPlayerAttributes

_LOG = logging.getLogger(__name__)

# Default polling interval in seconds
POLL_INTERVAL = 5

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

    Uses the pychannels client to communicate with the Channels HTTP API.
    Polls the device every POLL_INTERVAL seconds to keep state up to date.
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

        self._client = ChannelsClient(host=device_config.address, port=device_config.port)

        self._power_state: media_player.States = media_player.States.UNKNOWN

        self.attributes = MediaPlayerAttributes(
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
    def state(self) -> media_player.States | None:
        return self._power_state

    @property
    def log_id(self) -> str:
        return self.name if self.name else self.identifier

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
        await self._refresh_entities()
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
                self._power_state = media_player.States.UNAVAILABLE
                self.attributes.STATE = media_player.States.UNAVAILABLE
            else:
                self._update_state_from_status(status)
        except Exception as err:  # pylint: disable=broad-exception-caught
            _LOG.error("[%s] Error polling Channels app: %s", self.log_id, err)
            self._power_state = media_player.States.UNAVAILABLE
            self.attributes.STATE = media_player.States.UNAVAILABLE

        await self._refresh_entities()

    async def _refresh_entities(self) -> None:
        """Push current attributes to all registered entities via the driver."""
        if self._driver is None:
            # Fallback: emit raw UPDATE event if no driver reference
            self.events.emit(DeviceEvents.UPDATE, update=self.attributes)
            return

        for entity in self._driver.filter_entities_by_type(
            EntityTypes.MEDIA_PLAYER, source=EntitySource.CONFIGURED
        ):
            if isinstance(entity, FrameworkEntity):
                entity.update(self.attributes)

    def _update_state_from_status(self, status: dict[str, Any]) -> None:
        channels_status = status.get("status", "stopped")
        self._power_state = _CHANNELS_STATE_MAP.get(
            channels_status, media_player.States.UNKNOWN
        )
        self.attributes.STATE = self._power_state
        self.attributes.MUTED = status.get("muted", False)

        playback_time = status.get("playback_time")
        self.attributes.MEDIA_POSITION = (
            int(playback_time) if playback_time is not None else None
        )

        now_playing = status.get("now_playing")
        channel = status.get("channel")

        if now_playing:
            content_type = now_playing.get("type", "")
            if content_type == "movie":
                self.attributes.MEDIA_TYPE = media_player.MediaType.VIDEO
            else:
                self.attributes.MEDIA_TYPE = media_player.MediaType.TVSHOW

            title = now_playing.get("title")
            episode_title = now_playing.get("episode_title")
            if title and episode_title:
                self.attributes.MEDIA_TITLE = f"{title} - {episode_title}"
            elif title:
                self.attributes.MEDIA_TITLE = title
            else:
                self.attributes.MEDIA_TITLE = None

            self.attributes.MEDIA_ARTIST = (
                channel.get("name") if channel and channel.get("name") else None
            )

            image_url = now_playing.get("image_url") or now_playing.get("thumb_url")
            if not image_url and channel:
                image_url = channel.get("image_url")
            self.attributes.MEDIA_IMAGE_URL = image_url

            duration = now_playing.get("duration")
            self.attributes.MEDIA_DURATION = (
                int(duration) if duration is not None else None
            )

        elif channel:
            self.attributes.MEDIA_TYPE = media_player.MediaType.TVSHOW
            self.attributes.MEDIA_TITLE = channel.get("name")
            self.attributes.MEDIA_ARTIST = "Ch. " + channel.get("number", "")
            self.attributes.MEDIA_IMAGE_URL = channel.get("image_url")
            self.attributes.MEDIA_DURATION = None
        else:
            self.attributes.MEDIA_TYPE = None
            self.attributes.MEDIA_TITLE = None
            self.attributes.MEDIA_ARTIST = None
            self.attributes.MEDIA_IMAGE_URL = None
            self.attributes.MEDIA_DURATION = None

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
        current = self.attributes.MEDIA_POSITION or 0
        delta = position - current
        if delta != 0:
            await self._client.seek(delta)

    async def toggle_cc(self) -> None:
        _LOG.debug("[%s] Toggle closed captions", self.log_id)
        await self._client.toggle_cc()

    async def toggle_record(self) -> None:
        _LOG.debug("[%s] Toggle record", self.log_id)
        await self._client.toggle_record()

    def get_device_attributes(self, entity_id: str) -> MediaPlayerAttributes:
        return self.attributes
