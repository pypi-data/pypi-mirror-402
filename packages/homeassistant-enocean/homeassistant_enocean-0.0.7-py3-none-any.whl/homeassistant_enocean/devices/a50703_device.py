from .device import EnOceanDevice
from ..entity_properties import HomeAssistantEntityProperties


class EnOceanA50703Device(EnOceanDevice):
    """Handler for EnOcean Equipment Profile A5-07-03 (Occupancy with Supply voltage monitor and 10-bit illumination measurement)"""

    def initialize_entities(self) -> None:
        """Initialize the entities handled by this EEP handler."""
        self._binary_sensor_entities = [
            HomeAssistantEntityProperties(
                unique_id="motion_detected", device_class="motion"
            ),
        ]

        self._sensor_entities = [
            HomeAssistantEntityProperties(
                unique_id="supply_voltage",
                device_class="voltage",
                native_unit_of_measurement="V",
                entity_category="diagnostic",
            ),
            HomeAssistantEntityProperties(
                unique_id="illumination",
                native_unit_of_measurement="lx",
                device_class="illuminance",
            ),
        ]

    def handle_matching_packet(self, packet) -> None:
        """Handle an incoming EnOcean packet."""
        packet.parse_eep(0x07, 0x03)
        motion = packet.parsed["PIR"]["raw_value"]
        illumination = packet.parsed["ILL"]["raw_value"]
        supply_voltage = 5.0 * (
            packet.parsed["SVC"]["raw_value"] / 250.0
        )  # convert to volts from range 0..250 representing 0..5V

        motion_callback = self._binary_sensor_callbacks.get("motion_detected")
        if motion_callback:
            motion_callback(motion)

        illumination_callback = self._sensor_callbacks.get("illumination")
        if illumination_callback:
            illumination_callback(illumination)

        supply_voltage_callback = self._sensor_callbacks.get("supply_voltage")
        if supply_voltage_callback:
            supply_voltage_callback(supply_voltage)
