"""
Channels App Setup Flow.

Handles device setup via mDNS auto-discovery (_channels_app._tcp) with a
fallback to manual IP address entry.

:license: Mozilla Public License Version 2.0, see LICENSE for more details.
"""

import asyncio
import logging
from typing import Any

from pychannels import Channels

from const import DeviceConfig
from ucapi import IntegrationSetupError, RequestUserInput, SetupError
from ucapi_framework import BaseSetupFlow

_LOG = logging.getLogger(__name__)

CHANNELS_DEFAULT_PORT = 57000


class DeviceSetupFlow(BaseSetupFlow[DeviceConfig]):
    """
    Setup flow for the Channels app integration.

    Supports automatic discovery via mDNS and manual IP entry fallback.
    """

    def get_manual_entry_form(self) -> RequestUserInput:
        """
        Return the manual entry form for Channels app setup.

        Only an IP address is required - the port is always 57000.
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
                                    "Enter the IP address of the device running the Channels app. "
                                    "The app must be open and running on port 57000."
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

        if not address:
            _LOG.warning("No address provided, re-displaying form")
            return self.get_manual_entry_form()

        if not name:
            name = f"Channels ({address})"

        _LOG.debug("Attempting to connect to Channels app at %s", address)

        try:
            # Use pychannels to verify connectivity
            client = Channels(host=address, port=CHANNELS_DEFAULT_PORT)
            status = await asyncio.get_event_loop().run_in_executor(None, client.status)

            if status.get("status") == "offline":
                _LOG.error("Channels app at %s is offline or unreachable", address)
                return SetupError(IntegrationSetupError.CONNECTION_REFUSED)

            _LOG.info(
                "Successfully connected to Channels app at %s (status: %s)",
                address,
                status.get("status"),
            )

            # Use IP address (with dots replaced) as stable identifier
            identifier = address.replace(".", "_")

            return DeviceConfig(
                identifier=identifier,
                name=name,
                address=address,
            )

        except Exception as ex:
            _LOG.error("Failed to connect to Channels app at %s: %s", address, ex)
            return SetupError(IntegrationSetupError.CONNECTION_REFUSED)
