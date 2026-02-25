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
from ucapi import MediaPlayer, media_player, EntityTypes
from ucapi.media_player import DeviceClasses, Attributes, Features, Commands

import device
from const import DeviceConfig, SimpleCommands
from ucapi_framework import create_entity_id
from ucapi_framework.entity import Entity as FrameworkEntity

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
]


class ChannelsMediaPlayer(MediaPlayer, FrameworkEntity):
    """
    Media Player entity for the Channels app.

    Maps ucapi media player commands to Channels API calls via the Device class.
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
                Attributes.STATE: device_instance.state,
                Attributes.MUTED: False,
                Attributes.MEDIA_TYPE: None,
                Attributes.MEDIA_TITLE: None,
                Attributes.MEDIA_ARTIST: None,
                Attributes.MEDIA_IMAGE_URL: None,
                Attributes.MEDIA_POSITION: None,
                Attributes.MEDIA_DURATION: None,
            },
            device_class=DeviceClasses.SET_TOP_BOX,
            options={
                media_player.Options.SIMPLE_COMMANDS: [
                    member.value for member in SimpleCommands
                ]
            },
            cmd_handler=self.handle_command,
        )

    async def handle_command(
        self,
        _entity: MediaPlayer,
        cmd_id: str,
        params: dict[str, Any] | None,
        __: Any | None = None,
    ) -> ucapi.StatusCodes:
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

                case _:
                    _LOG.warning("Unhandled command: %s", cmd_id)
                    return ucapi.StatusCodes.NOT_IMPLEMENTED

            self.update(self._device.attributes)
            return ucapi.StatusCodes.OK

        except Exception as ex:  # pylint: disable=broad-exception-caught
            _LOG.error("Error executing command %s: %s", cmd_id, ex)
            return ucapi.StatusCodes.BAD_REQUEST
