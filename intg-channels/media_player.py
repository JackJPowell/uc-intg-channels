"""
Channels App Media Player Entity.

Implements the ucapi MediaPlayer entity for the Channels app.
Supports full playback controls including play, pause, stop, seek,
channel up/down, mute, and media metadata.

:license: Mozilla Public License Version 2.0, see LICENSE for more details.
"""

import logging
from typing import Any

import ucapi
from ucapi import media_player, EntityTypes, BrowseOptions, BrowseResults
from ucapi.media_player import DeviceClasses, Attributes, Features, Commands

import browser as channels_browser
import device
from const import DeviceConfig, SimpleCommands
from ucapi_framework import create_entity_id, MediaPlayerEntity

_LOG = logging.getLogger(__name__)

FEATURES = [
    Features.PLAY_PAUSE,
    Features.STOP,
    Features.NEXT,
    Features.PREVIOUS,
    Features.FAST_FORWARD,
    Features.REWIND,
    Features.MUTE_TOGGLE,
    Features.SEEK,
    Features.MEDIA_DURATION,
    Features.MEDIA_POSITION,
    Features.MEDIA_TITLE,
    Features.MEDIA_ARTIST,
    Features.MEDIA_IMAGE_URL,
    Features.MEDIA_TYPE,
    Features.CHANNEL_SWITCHER,
    Features.BROWSE_MEDIA,
    Features.PLAY_MEDIA,
]


class ChannelsMediaPlayer(MediaPlayerEntity):
    """
    Media Player entity for the Channels app.

    Uses the coordinator pattern: subscribes to device UPDATE events via
    subscribe_to_device() and syncs state through sync_state().
    """

    def __init__(self, config_device: DeviceConfig, device_instance: device.Device):
        self._device = device_instance
        entity_id = create_entity_id(EntityTypes.MEDIA_PLAYER, config_device.identifier)

        _LOG.debug("Initializing Channels media player entity: %s", entity_id)

        super().__init__(
            entity_id,
            config_device.name,
            FEATURES,
            attributes={
                Attributes.STATE: media_player.States.UNKNOWN,
                Attributes.MUTED: False,
                Attributes.MEDIA_TYPE: None,
                Attributes.MEDIA_TITLE: None,
                Attributes.MEDIA_ARTIST: None,
                Attributes.MEDIA_IMAGE_URL: None,
                Attributes.MEDIA_POSITION: None,
                Attributes.MEDIA_DURATION: None,
            },
            device_class=DeviceClasses.SPEAKER,
            options={
                media_player.Options.SIMPLE_COMMANDS: [
                    member.value for member in SimpleCommands
                ]
            },
            cmd_handler=self.handle_command,
        )

        self.subscribe_to_device(device_instance)

    async def sync_state(self) -> None:
        """Pull current attributes from the device and push to the Remote."""
        if self._device is None:
            return
        self.update(self._device.get_media_player_attributes())

    async def handle_command(
        self,
        _entity: MediaPlayerEntity,
        cmd_id: str,
        params: dict[str, Any] | None,
        __: Any | None = None,
    ) -> ucapi.StatusCodes:
        if self._device is None:
            return ucapi.StatusCodes.SERVICE_UNAVAILABLE

        _LOG.info("Received command: %s %s", cmd_id, params if params else "")

        try:
            match cmd_id:
                case Commands.PLAY_PAUSE:
                    await self._device.play_pause()

                case Commands.STOP:
                    await self._device.stop()

                case Commands.NEXT:
                    # Next = channel up
                    await self._device.channel_up()

                case Commands.PREVIOUS:
                    # Previous = previous channel (last watched)
                    await self._device.previous_channel()

                case Commands.FAST_FORWARD:
                    await self._device.skip_forward()

                case Commands.REWIND:
                    await self._device.skip_backward()

                case Commands.MUTE_TOGGLE:
                    await self._device.mute_toggle()

                case Commands.SEEK:
                    position = params.get("media_position") if params else None
                    if position is not None:
                        await self._device.seek(int(position))
                    else:
                        _LOG.warning("SEEK command missing media_position param")
                        return ucapi.StatusCodes.BAD_REQUEST

                case Commands.CHANNEL_UP:
                    await self._device.channel_up()

                case Commands.CHANNEL_DOWN:
                    await self._device.channel_down()

                # Simple commands
                case SimpleCommands.TOGGLE_CC:
                    await self._device.toggle_cc()

                case SimpleCommands.TOGGLE_PIP:
                    await self._device.toggle_pip()

                case SimpleCommands.TOGGLE_RECORD:
                    await self._device.toggle_record()

                case SimpleCommands.SEEK_FORWARD:
                    await self._device.seek_forward()

                case SimpleCommands.SEEK_BACKWARD:
                    await self._device.seek_backward()

                case Commands.PLAY_MEDIA:
                    return await self._handle_play_media(params)

                case _:
                    _LOG.warning("Unhandled command: %s", cmd_id)
                    return ucapi.StatusCodes.NOT_IMPLEMENTED

            return ucapi.StatusCodes.OK

        except Exception as ex:  # pylint: disable=broad-exception-caught
            _LOG.error("Error executing command %s: %s", cmd_id, ex)
            return ucapi.StatusCodes.BAD_REQUEST

    async def browse(self, options: BrowseOptions) -> BrowseResults | ucapi.StatusCodes:
        """Handle a browse_media request from the Remote."""
        if self._device is None:
            _LOG.warning("browse called but no device is connected")
            return ucapi.StatusCodes.SERVICE_UNAVAILABLE
        return await channels_browser.browse(self._device, options)

    async def _handle_play_media(self, params: dict | None) -> ucapi.StatusCodes:
        """Play a DVR recording or movie on the Channels app."""
        if not params or not (media_id := params.get("media_id")):
            _LOG.warning("play_media called without media_id")
            return ucapi.StatusCodes.BAD_REQUEST

        try:
            await self._device._client.play_recording(media_id)  # pylint: disable=protected-access
            _LOG.info("play_media: started playback of recording id=%s", media_id)
            return ucapi.StatusCodes.OK
        except Exception as ex:  # pylint: disable=broad-exception-caught
            _LOG.error("play_media failed for media_id=%s: %s", media_id, ex)
            return ucapi.StatusCodes.SERVER_ERROR
