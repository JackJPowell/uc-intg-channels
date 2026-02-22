# Unfolded Circle Channels Integration

Control the [Channels app](https://getchannels.com/) from your [Unfolded Circle Remote Two/3](https://www.unfoldedcircle.com/). Supports live TV, DVR playback, and more via the Channels HTTP API.

Built with the [ucapi-framework](https://github.com/jackjpowell/ucapi-framework).

## Features

- **Automatic discovery** via mDNS (`_channels_app._tcp`) with manual IP fallback
- **Media player entity** with full playback control:
  - Play/Pause, Stop
  - Channel Up/Down, Previous Channel
  - Skip Forward/Backward (chapter marks)
  - Seek Forward/Backward
  - Mute Toggle
  - Now playing metadata: title, episode, artwork, position, duration
- **Simple commands**: Toggle Closed Captions, Toggle Record, Seek Forward, Seek Backward
- Polls the Channels app every 10 seconds (configurable)

## Requirements

- [Channels app](https://getchannels.com/) running on Apple TV, NVIDIA SHIELD, or other supported device
- Channels app must be reachable on port `57000` from the Remote

## Project Structure

```
├── driver.json              # Integration metadata and configuration
├── intg-channels/
│   ├── const.py             # Constants and device configuration dataclass
│   ├── device.py            # Device communication and state management
│   ├── discover.py          # mDNS device discovery
│   ├── driver.py            # Main entry point
│   ├── media_player.py      # Media player entity
│   └── setup.py             # Setup flow and user configuration
├── Dockerfile               # Container build configuration
└── requirements.txt         # Python dependencies
```

## Development

### Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip

### Local Development

1. Install dependencies:
   ```bash
   uv sync
   ```

2. Run the integration:
   ```bash
   python intg-channels/driver.py
   ```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `UC_LOG_LEVEL` | Logging level (DEBUG, INFO, WARNING, ERROR) | `DEBUG` |
| `UC_CONFIG_HOME` | Configuration directory path | `/config` |
| `UC_INTEGRATION_INTERFACE` | Network interface to bind | `0.0.0.0` |
| `UC_INTEGRATION_HTTP_PORT` | HTTP port for the integration | `9090` |
| `UC_DISABLE_MDNS_PUBLISH` | Disable mDNS advertisement | `false` |
| `UC_CHANNELS_POLL_INTERVAL` | Polling interval in seconds | `10` |

## Deployment

### Install on Remote

1. Build the integration package (tar.gz file)
2. Upload via the Remote's web configurator under Integrations
3. The integration will scan for Channels app instances on your network automatically, or prompt you to enter the IP address manually

### Docker

```bash
docker run -d \
  --name=uc-intg-channels \
  --network host \
  -v $(pwd)/config:/config \
  --restart unless-stopped \
  ghcr.io/jackjpowell/uc-intg-channels:latest
```

### Docker Compose

```yaml
services:
  uc-intg-channels:
    image: ghcr.io/jackjpowell/uc-intg-channels:latest
    container_name: uc-intg-channels
    network_mode: host
    volumes:
      - ./config:/config
    restart: unless-stopped
```

## Resources

- [Channels App](https://getchannels.com/)
- [UCAPI Framework](https://github.com/jackjpowell/ucapi-framework)
- [UC Integration Python Library](https://github.com/aitatoi/integration-python-library)
- [Unfolded Circle Developer Documentation](https://github.com/unfoldedcircle/core-api)

## License

Mozilla Public License Version 2.0 - see [LICENSE](LICENSE) for details.
