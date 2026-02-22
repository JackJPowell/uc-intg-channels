# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## Unreleased

### Changed

- Port is now configurable per device (default: 57000) and exposed as an optional field in the setup flow
- Replaced pychannels dependency with a native async HTTP client

---

## v0.1.0 — 2026-02-21

Initial release.

### Added

- Media player entity with play/pause, stop, channel up/down, previous channel, skip forward/backward, seek, and mute toggle
- Now playing metadata: title, episode title, artwork, position, and duration
- Simple commands: Toggle Closed Captions, Toggle Record, Seek Forward, Seek Backward
- Automatic discovery via mDNS (`_channels_app._tcp`) with manual IP address fallback
- Configurable polling interval via `UC_CHANNELS_POLL_INTERVAL` (default: 10s)
- Optional port configuration in setup flow (default: 57000)
