"""
Claude Board Bluetooth Module (Phase 2 - Planned)

This module will provide Bluetooth Low Energy (BLE) connectivity
for the physical console device.

Features planned:
- BLE GATT Server for receiving button presses
- BLE GATT Client for sending state updates
- Auto-discovery and pairing
- Reconnection handling

Hardware planned:
- Raspberry Pi 4B or ESP32-S3
- 4 mechanical key switches (Cherry MX compatible)
- E-ink display (2.9" or 4.2")
- Buzzer for audio feedback
- LED status indicators
"""

# Placeholder for future implementation
__all__ = []


class BLENotImplementedError(NotImplementedError):
    """Raised when BLE functionality is called but not yet implemented."""

    def __init__(self):
        super().__init__(
            "Bluetooth support is planned for Phase 2. "
            "Currently only the web UI is available. "
            "Run 'claude-board serve' to use the web interface."
        )


def connect():
    """Connect to a Claude Board physical device via Bluetooth."""
    raise BLENotImplementedError()


def scan():
    """Scan for available Claude Board devices."""
    raise BLENotImplementedError()


def pair():
    """Pair with a Claude Board device."""
    raise BLENotImplementedError()
