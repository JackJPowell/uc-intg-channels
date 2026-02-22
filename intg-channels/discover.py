"""
Channels App Discovery Module.

Discovers Channels app instances on the local network using mDNS.
The Channels app advertises itself via Bonjour with the service type
_channels_app._tcp.

:license: Mozilla Public License Version 2.0, see LICENSE for more details.
"""

import logging
from typing import Any

from ucapi_framework import DiscoveredDevice
from ucapi_framework.discovery import MDNSDiscovery

_LOG = logging.getLogger(__name__)

CHANNELS_MDNS_SERVICE = "_channels_app._tcp.local."
CHANNELS_DEFAULT_PORT = 57000


class DeviceDiscovery(MDNSDiscovery):
    """
    Discover Channels app instances on the local network.

    Uses mDNS (Bonjour) to find devices advertising the _channels_app._tcp service.
    """

    def parse_mdns_service(self, service_info: Any) -> DiscoveredDevice | None:
        """
        Parse a mDNS service record into a DiscoveredDevice.

        :param service_info: zeroconf ServiceInfo object
        :return: DiscoveredDevice or None if parsing fails
        """
        try:
            # Get IP address from service info
            addresses = service_info.parsed_addresses()
            if not addresses:
                _LOG.debug("Skipping service with no addresses: %s", service_info.name)
                return None

            address = addresses[0]

            # Use service name as device name, stripping the service type suffix
            raw_name = service_info.name
            # Strip the service type (e.g., "Channels._channels_app._tcp.local." -> "Channels")
            name = raw_name.split(".")[0] if "." in raw_name else raw_name

            # Use address as identifier (stable across restarts)
            identifier = address.replace(".", "_")

            port = service_info.port or CHANNELS_DEFAULT_PORT

            _LOG.debug(
                "Discovered Channels app: name=%s, address=%s, port=%d",
                name,
                address,
                port,
            )

            return DiscoveredDevice(
                identifier=identifier,
                name=name,
                address=address,
                extra_data={"port": port},
            )

        except Exception as err:  # pylint: disable=broad-exception-caught
            _LOG.warning("Failed to parse mDNS service info: %s", err)
            return None
