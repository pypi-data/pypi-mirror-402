# NODON Sin 2-2-01
# https://www.enocean-alliance.org/wp-content/uploads/2017/10/NodOn-SIN-2-2-0x-UserGuide-170731-DE-interactive.pdf


from homeassistant_enocean.devices.device import EnOceanDevice
from homeassistant_enocean.entity_properties import HomeAssistantEntityProperties
from homeassistant_enocean.types import EnOceanEntityUID

from enocean.protocol.packet import RadioPacket


class EnOceanD201XXDevice(EnOceanDevice):
    """Handler for EnOcean Equipment Profiles D2-01-00 - D2-01-14"""

    def initialize_entities(self) -> None:
        """Initialize the entities handled by this EEP handler."""
        # D2-01-00 to D2-01-0F have 1 channel, D2-01-10 to D2-01-12 have 2 channels, D2-01-13 has 4 channels, D2-01-14 has 8 channels

        if self.device_type.eep.type in (0x10, 0x11, 0x12):
            self._switch_entities = [
                HomeAssistantEntityProperties(unique_id="switch_1"),
                HomeAssistantEntityProperties(unique_id="switch_2"),
            ]

        elif self.device_type.eep.type == 0x13:
            self._switch_entities = [
                HomeAssistantEntityProperties(unique_id="switch_1"),
                HomeAssistantEntityProperties(unique_id="switch_2"),
                HomeAssistantEntityProperties(unique_id="switch_3"),
                HomeAssistantEntityProperties(unique_id="switch_4"),
            ]
        elif self.device_type.eep.type == 0x14:
            self._switch_entities = [
                HomeAssistantEntityProperties(unique_id="switch_1"),
                HomeAssistantEntityProperties(unique_id="switch_2"),
                HomeAssistantEntityProperties(unique_id="switch_3"),
                HomeAssistantEntityProperties(unique_id="switch_4"),
                HomeAssistantEntityProperties(unique_id="switch_5"),
                HomeAssistantEntityProperties(unique_id="switch_6"),
                HomeAssistantEntityProperties(unique_id="switch_7"),
                HomeAssistantEntityProperties(unique_id="switch_8"),
            ]

        else:
            self._switch_entities = [
                HomeAssistantEntityProperties(unique_id=None),
            ]

    def handle_matching_packet(self, packet) -> None:
        """Handle an incoming EnOcean packet."""
        packet.parse_eep(0x01, self.device_type.eep.type)
        if packet.parsed["CMD"]["raw_value"] != 4:
            return

        channel = packet.parsed["IO"]["raw_value"]
        output = packet.parsed["OV"]["raw_value"]

        # print(f"EnOcean D2-01-{self.device_type.eep.type:02X} switch channel {channel} output {output}")

        callback = None
        if self.device_type.eep.type in (0x10, 0x11, 0x12, 0x13, 0x14):
            callback = self._switch_callbacks.get(f"switch_{channel + 1}")
        else:
            callback = self._switch_callbacks.get(None)

        if callback:
            callback(output > 0)

    def _get_channel_from_entity_uid(self, entity_uid: EnOceanEntityUID) -> int:
        if len(self._switch_entities) == 1:
            return 0

        channel = 0
        if entity_uid.startswith("switch_"):
            try:
                channel = int(entity_uid.split("_")[1]) - 1
            except Exception:
                print(
                    "EnOceanD201XXDevice._get_channel_from_entity_uid: Invalid entity_uid format for switch entity."
                )

        return channel

    def switch_turn_on(self, entity_uid: EnOceanEntityUID) -> None:
        """Turn on the switch."""
        channel = self._get_channel_from_entity_uid(entity_uid)

        packet = RadioPacket.create(
            rorg=self.device_type.eep.rorg,
            rorg_func=self.device_type.eep.func,
            rorg_type=self.device_type.eep.type,
            command=0x01,  # actuator set output
            destination=self.enocean_id.to_bytelist(),
            sender=self.sender_id.to_bytelist(),
            DV=0x00,  # switch to new output value
            IO=channel,
            OV=100,  # output value on (100%)
        )
        self.send_packet(packet)

    def switch_turn_off(self, entity_uid: EnOceanEntityUID) -> None:
        """Turn off the switch."""
        channel = self._get_channel_from_entity_uid(entity_uid)

        packet = RadioPacket.create(
            rorg=self.device_type.eep.rorg,
            rorg_func=self.device_type.eep.func,
            rorg_type=self.device_type.eep.type,
            command=0x01,  # actuator set output
            destination=self.enocean_id.to_bytelist(),
            sender=self.sender_id.to_bytelist(),
            DV=0x00,  # switch to new output value
            IO=channel,
            OV=0,  # output value off (0%)
        )
        self.send_packet(packet)
