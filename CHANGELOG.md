# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## Unreleased

## v0.2.0 — 2026-04-10

### Added

- Media browsing support with a structured library hierarchy (TV Shows → Episodes, Movies)
- Play media command, allowing items selected from the browser to be queued and played on the active Channels client
- `browse_media` and `play_media` features registered on the media player entity

---

## v0.1.5 — 2026-03-09

### Changes

- Under the hood changes to simply future development

---

## v0.1.4 — 2026-02-24

### Added

- Toggle Picture in Picture simple command

### Changed

- Setup now correctly asks for the IP address of the device running the Channels client app, not the DVR server
- Port is now configurable in the setup flow (default: 57000)

### Removed

- mDNS auto-discovery removed; the Channels client app requires manual IP entry

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
