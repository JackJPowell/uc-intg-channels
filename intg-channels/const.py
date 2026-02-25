"""
Constants for the Channels App Integration.

:license: Mozilla Public License Version 2.0, see LICENSE for more details.
"""

from dataclasses import dataclass
from enum import StrEnum


DEFAULT_PORT = 57000


@dataclass
class DeviceConfig:
    """Configuration for a Channels app device."""

    identifier: str
    """Unique identifier of the device (derived from IP address)."""

    name: str
    """Friendly name of the device for display purposes."""

    address: str
    """IP address or hostname of the Channels app device."""

    port: int = DEFAULT_PORT
    """Port the Channels app is listening on (default: 57000)."""


class SimpleCommands(StrEnum):
    """
    Additional simple commands specific to the Channels app.

    These appear as buttons the user can assign in the remote configurator.
    """

    TOGGLE_CC = "Toggle Closed Captions"
    TOGGLE_RECORD = "Toggle Record"
    TOGGLE_PIP = "Toggle Picture in Picture"
    SEEK_FORWARD = "Seek Forward"
    SEEK_BACKWARD = "Seek Backward"
