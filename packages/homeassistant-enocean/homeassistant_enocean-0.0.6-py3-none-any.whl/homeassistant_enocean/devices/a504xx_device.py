from .device import EnOceanDevice
from ..entity_properties import HomeAssistantEntityProperties


class EnOceanA504XXDevice(EnOceanDevice):
    """Handler for EnOcean Equipment Profile A5-02 Family Temperature and humidity Sensors."""

    def initialize_entities(self) -> None:
        """Initialize the entities handled by this EEP handler."""
        self._sensor_entities = [
            HomeAssistantEntityProperties(
                unique_id="temperature",
                device_class="temperature",
                native_unit_of_measurement="°C",
            ),
            HomeAssistantEntityProperties(
                unique_id="humidity",
                device_class="humidity",
                native_unit_of_measurement="%",
            ),
        ]

    def handle_matching_packet(self, packet) -> None:
        """Handle an incoming EnOcean packet."""
        try:
            packet.parse_eep(rorg_func=0x04, rorg_type=self.device_type.eep.type)
            temperature = packet.parsed["TMP"]["value"]
            humidity = packet.parsed["HUM"]["value"]

            temperature_callback = self._sensor_callbacks.get("temperature")
            if temperature_callback:
                temperature_callback(temperature)

            humidity_callback = self._sensor_callbacks.get("humidity")
            if humidity_callback:
                humidity_callback(humidity)
        except Exception:
            return
