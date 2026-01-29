from homeassistant_enocean.devices.device import EnOceanDevice
from homeassistant_enocean.entity_properties import HomeAssistantEntityProperties
from homeassistant_enocean.types import EnOceanBinarySensorCallback
from enocean.protocol.packet import RadioPacket

BUTTON_ACTION_UID_MAP = {
    0x30: "a0",
    0x10: "a1",
    0x70: "b0",
    0x50: "b1",
    0x37: "ab0",
    0x15: "ab1",
    0x17: "a1b0",
    0x35: "a0b1",
}
"""Mapping of button action codes to unique IDs for EnOcean F6-02-XX devices."""


class EnOceanF602XXDevice(EnOceanDevice):
    """Handler for EnOcean Equipment Profiles F6-02-01/02"""

    def initialize_entities(self) -> None:
        """Initialize the entities handled by this EEP handler."""
        self._binary_sensor_entities = [
            HomeAssistantEntityProperties(
                unique_id=name,
            )
            for name in BUTTON_ACTION_UID_MAP.values()
        ]

    def handle_matching_packet(self, packet: RadioPacket) -> None:
        """Handle an incoming EnOcean packet."""
        action = packet.data[1]

        # handle button release (all buttons)
        if action == 0x00:
            for callback in self._binary_sensor_callbacks.values():
                callback(False)
            return

        # handle button press
        callback: EnOceanBinarySensorCallback | None = None
        callback = self._binary_sensor_callbacks.get(BUTTON_ACTION_UID_MAP.get(action))

        if callback:
            callback(True)
