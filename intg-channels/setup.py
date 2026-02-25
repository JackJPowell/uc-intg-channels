"""
Channels App Setup Flow.

Handles device setup via mDNS auto-discovery (_channels_app._tcp) with a
fallback to manual IP address entry.

:license: Mozilla Public License Version 2.0, see LICENSE for more details.
"""

import logging
from typing import Any

from api import ChannelsClient
from const import DEFAULT_PORT, DeviceConfig
from ucapi import IntegrationSetupError, RequestUserInput, SetupError
from ucapi_framework import BaseSetupFlow

_LOG = logging.getLogger(__name__)


class DeviceSetupFlow(BaseSetupFlow[DeviceConfig]):
    """
    Setup flow for the Channels app integration.

    Supports automatic discovery via mDNS and manual IP entry fallback.
    """

    def get_manual_entry_form(self) -> RequestUserInput:
        """
        Return the manual entry form for Channels app setup.

        IP address is required; port defaults to 57000 and name is optional.
        """
        return RequestUserInput(
            {"en": "Channels App Setup"},
            [
                {
                    "id": "info",
                    "label": {"en": "Connect to Channels App"},
                    "field": {
                        "label": {
                            "value": {
                                "en": (
                                    "Enter the IP address of the Apple TV, NVIDIA SHIELD, or other "
                                    "device running the Channels client app — not the Channels DVR server. "
                                    "The app must be open and reachable on port 57000."
                                ),
                            }
                        }
                    },
                },
                {
                    "field": {"text": {"value": ""}},
                    "id": "address",
                    "label": {"en": "IP Address"},
                },
                {
                    "field": {"number": {"value": DEFAULT_PORT, "min": 1, "max": 65535}},
                    "id": "port",
                    "label": {"en": "Port (optional)"},
                },
                {
                    "field": {"text": {"value": ""}},
                    "id": "name",
                    "label": {"en": "Device Name (optional)"},
                },
            ],
        )

    async def query_device(
        self, input_values: dict[str, Any]
    ) -> DeviceConfig | SetupError | RequestUserInput:
        """
        Validate the Channels app connection and build a DeviceConfig.

        :param input_values: User input from manual entry or discovery
        :return: DeviceConfig on success, SetupError on failure
        """
        address = input_values.get("address", "").strip()
        name = input_values.get("name", "").strip()
        try:
            port = int(input_values.get("port", DEFAULT_PORT))
        except (ValueError, TypeError):
            port = DEFAULT_PORT

        if not address:
            _LOG.warning("No address provided, re-displaying form")
            return self.get_manual_entry_form()

        if not name:
            name = f"Channels ({address})"

        _LOG.debug("Attempting to connect to Channels app at %s:%d", address, port)

        try:
            client = ChannelsClient(host=address, port=port)
            status = await client.status()

            if status.get("status") == "offline":
                _LOG.error("Channels app at %s:%d is offline or unreachable", address, port)
                return SetupError(IntegrationSetupError.CONNECTION_REFUSED)

            _LOG.info(
                "Successfully connected to Channels app at %s:%d (status: %s)",
                address,
                port,
                status.get("status"),
            )

            identifier = address.replace(".", "_")

            return DeviceConfig(
                identifier=identifier,
                name=name,
                address=address,
                port=port,
            )

        except Exception as ex:
            _LOG.error("Failed to connect to Channels app at %s:%d: %s", address, port, ex)
            return SetupError(IntegrationSetupError.CONNECTION_REFUSED)
