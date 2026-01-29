from .device import EnOceanDevice
from ..entity_properties import HomeAssistantEntityProperties


class EnOceanA50601Device(EnOceanDevice):
    """Handler for EnOcean Equipment Profile A5-06-01 Light sensor (incl. the modified Eltako variant with MAN_ID = 0x0D)."""

    def initialize_entities(self) -> None:
        """Initialize the entities handled by this EEP handler."""
        self._sensor_entities = [
            HomeAssistantEntityProperties(
                unique_id=None,
                device_class="illuminance",
                native_unit_of_measurement="lx",
            ),
        ]

        if not self._is_eltako_variant():
            # Eltako variant does not have SVC (supply voltage) measurement, as it uses that databit for illuminance measurement 0-100
            self._sensor_entities.append(
                HomeAssistantEntityProperties(
                    unique_id="supply_voltage",
                    device_class="voltage",
                    native_unit_of_measurement="V",
                    entity_category="diagnostic",
                ),
            )

    def handle_matching_packet(self, packet) -> None:
        """Handle an incoming EnOcean packet."""
        try:
            packet.parse_eep(rorg_func=0x06, rorg_type=0x01)
            illumination: float = 0

            if self._is_eltako_variant():
                ill2 = packet.parsed["ILL2"]["value"]
                if ill2 > 300:
                    illumination = round(ill2)
                else:
                    illumination = packet.parsed["SVC"]["raw_value"]

            else:
                svc = packet.parsed["SVC"]["value"]
                supply_voltage_callback = self._sensor_callbacks.get("supply_voltage")
                if supply_voltage_callback:
                    supply_voltage_callback(svc)

                rs = packet.parsed["RS"]["raw_value"]
                if rs == 0:
                    illumination = packet.parsed["ILL1"]["value"]
                else:
                    illumination = packet.parsed["ILL2"]["value"]

            illumination_callback = self._sensor_callbacks.get(None)
            if illumination_callback:
                illumination_callback(illumination)

        except Exception:
            return

    def _is_eltako_variant(self) -> bool:
        return (
            self.device_type.eep.manufacturer_id is not None
            and self.device_type.eep.manufacturer_id == 0x0D
        )
