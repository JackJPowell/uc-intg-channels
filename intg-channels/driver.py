"""
Channels App Integration Driver.

Main entry point for the Channels app integration for Unfolded Circle Remote.

:copyright: (c) 2025 by Jack Powell.
:license: Mozilla Public License Version 2.0, see LICENSE for more details.
"""

import asyncio
import logging
import os

from const import DeviceConfig
from device import Device
from media_player import ChannelsMediaPlayer
from setup import DeviceSetupFlow
from ucapi_framework import BaseConfigManager, BaseIntegrationDriver, get_config_path


async def main():
    """Start the Channels app Remote integration driver."""
    logging.basicConfig()

    level = os.getenv("UC_LOG_LEVEL", "DEBUG").upper()
    logging.getLogger("driver").setLevel(level)
    logging.getLogger("media_player").setLevel(level)
    logging.getLogger("device").setLevel(level)
    logging.getLogger("setup").setLevel(level)

    driver = BaseIntegrationDriver(
        device_class=Device,
        entity_classes=[ChannelsMediaPlayer],  # type: ignore[arg-type]
    )

    driver.config_manager = BaseConfigManager(
        get_config_path(driver.api.config_dir_path),
        driver.on_device_added,
        driver.on_device_removed,
        config_class=DeviceConfig,
    )

    await driver.register_all_configured_devices()

    setup_handler = DeviceSetupFlow.create_handler(driver)

    await driver.api.init("driver.json", setup_handler)

    await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())
