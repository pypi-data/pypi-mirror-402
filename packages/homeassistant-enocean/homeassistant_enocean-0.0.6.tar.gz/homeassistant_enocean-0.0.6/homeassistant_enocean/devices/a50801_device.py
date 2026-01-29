from .device import EnOceanDevice
from ..entity_properties import HomeAssistantEntityProperties


class EnOceanA50801Device(EnOceanDevice):
    """Handler for EnOcean Equipment Profile A5-08-01 Light, temperature and occupancy sensor, range 0lx to 510lx, 0°C to 51°C and occupancy button (incl. the modified Eltako variant with MAN_ID = 0x0D)."""

    def initialize_entities(self) -> None:
        """Initialize the entities handled by this EEP handler."""
        self._binary_sensor_entities = [
            HomeAssistantEntityProperties(unique_id=None, device_class="occupancy"),
        ]

        self._sensor_entities = [
            HomeAssistantEntityProperties(
                unique_id="illumination",
                device_class="illuminance",
                native_unit_of_measurement="lx",
            ),
            HomeAssistantEntityProperties(
                unique_id="supply_voltage",
                device_class="voltage",
                native_unit_of_measurement="V",
                entity_category="diagnostic",
            ),
        ]

        if not self._is_eltako_variant():
            # Eltako variant does not have an occupancy button or temperature measurement
            self._binary_sensor_entities.append(
                HomeAssistantEntityProperties(
                    unique_id="occupancy_button", device_class="button"
                ),
            )

            self._sensor_entities.append(
                HomeAssistantEntityProperties(
                    unique_id="temperature",
                    device_class="temperature",
                    native_unit_of_measurement="°C",
                ),
            )

    def handle_matching_packet(self, packet) -> None:
        """Handle an incoming EnOcean packet."""
        try:
            packet.parse_eep(rorg_func=0x08, rorg_type=0x01)
            svc = packet.parsed["SVC"]["value"]
            ill = packet.parsed["ILL"]["value"]
            pirs = packet.parsed["PIRS"]["raw_value"]

            supply_voltage_callback = self._sensor_callbacks.get("supply_voltage")
            if supply_voltage_callback:
                supply_voltage_callback(svc)

            illumination_callback = self._sensor_callbacks.get("illumination")
            if illumination_callback:
                illumination_callback(ill)

            occupancy_callback = self._binary_sensor_callbacks.get(None)
            if occupancy_callback:
                occupancy_callback(pirs)

            if self._is_eltako_variant():
                return

            # for non-Eltako variants,  also handle temperature and occupancy button
            tmp = packet.parsed["TMP"]["value"]
            occ = packet.parsed["OCC"]["raw_value"]

            occupancy_button_callback = self._binary_sensor_callbacks.get(
                "occupancy_button"
            )
            if occupancy_button_callback:
                occupancy_button_callback(occ)

            temperature_callback = self._sensor_callbacks.get("temperature")
            if temperature_callback:
                temperature_callback(tmp)

        except Exception as e:
            print(f"Error handling packet in EnOceanA50801Device: {e}")
            return

    def _is_eltako_variant(self) -> bool:
        return (
            self.device_type.eep.manufacturer_id is not None
            and self.device_type.eep.manufacturer_id == 0x0D
        )
