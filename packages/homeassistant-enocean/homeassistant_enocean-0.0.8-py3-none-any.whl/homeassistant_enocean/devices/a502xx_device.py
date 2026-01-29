from .device import EnOceanDevice
from ..entity_properties import HomeAssistantEntityProperties


class EnOceanA502XXDevice(EnOceanDevice):
    """Handler for EnOcean Equipment Profile A5-02 Family Temperature Sensors with 1 bit accuracy.

    These sensors differ only by the temperature measurement range.
    """

    def initialize_entities(self) -> None:
        """Initialize the entities handled by this EEP handler."""
        self._sensor_entities = [
            HomeAssistantEntityProperties(
                unique_id=None,
                device_class="temperature",
                native_unit_of_measurement="°C",
            ),
        ]

    def handle_matching_packet(self, packet) -> None:
        """Handle an incoming EnOcean packet."""
        try:
            packet.parse_eep(rorg_func=0x02, rorg_type=self.device_type.eep.type)
            temperature = packet.parsed["TMP"]["value"]

            temperature_callback = self._sensor_callbacks.get(None)
            if temperature_callback:
                temperature_callback(temperature)
        except Exception:
            return
