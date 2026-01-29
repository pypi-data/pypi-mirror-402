from homeassistant_enocean.types import EnOceanEntityUID
from .device import EnOceanDevice

from ..address import EnOceanAddress
from ..entity_properties import HomeAssistantEntityProperties

from enocean.protocol.packet import RadioPacket
from enocean.protocol.constants import RORG
from enum import Enum

WATCHDOG_TIMEOUT = 1
WATCHDOG_INTERVAL = 0.2
WATCHDOG_MAX_QUERIES = 10


class EnOceanCoverCommand(Enum):
    """The possible commands to be sent to an EnOcean cover."""

    SET_POSITION = 1
    STOP = 2
    QUERY_POSITION_AND_ANGLE = 3


class EnOceanD20500Device(EnOceanDevice):
    """Handler for EnOcean Equipment Profile D2-05-00"""

    def initialize_entities(self) -> None:
        """Initialize the entities handled by this EEP handler."""
        self._cover_entities = [
            HomeAssistantEntityProperties(supported_features=1 | 2 | 4 | 8)
        ]  # open, close, stop, set position
        self._button_entities = [
            HomeAssistantEntityProperties(
                unique_id="query_state", entity_category="diagnostic"
            )
        ]

    def handle_matching_packet(self, packet) -> None:
        """Handle an incoming EnOcean packet."""

        # position is inversed in Home Assistant and in EnOcean:
        # 0 means 'closed' in Home Assistant and 'open' in EnOcean
        # 100 means 'open' in Home Assistant and 'closed' in EnOcean
        new_position = 100 - packet.data[1]

        # print(f"Received EnOcean cover position: {new_position} for device {enocean_id.to_string()}")
        callback = self._cover_callbacks.get(None)
        if not callback:
            return

        callback(new_position)

    def __send_cover_command(
        self,
        command: EnOceanCoverCommand,
        destination: EnOceanAddress,
        sender: EnOceanAddress,
        position: int = 0,
    ) -> None:
        """Send an EnOcean telegram with the respective command."""

        if command == EnOceanCoverCommand.SET_POSITION:
            packet = RadioPacket.create(
                rorg=RORG.VLD,
                rorg_func=0x05,
                rorg_type=0x00,
                destination=destination.to_bytelist(),
                sender=sender.to_bytelist(),
                command=command.value,
                POS=position,
            )
            # print(f"Sending EnOcean cover command {command.name} with position {position} ")
            self.send_packet(packet)
        else:
            packet = RadioPacket.create(
                rorg=RORG.VLD,
                rorg_func=0x05,
                rorg_type=0x00,
                destination=destination.to_bytelist(),
                sender=sender.to_bytelist(),
                command=command.value,
            )
            # print(f"Sending EnOcean cover command {command.name}")
            self.send_packet(packet)

    def set_cover_position(self, entity_uid: EnOceanEntityUID, position: int) -> None:
        """Set the position of a cover device (0 = closed, 100 = open)."""
        enocean_position = 100 - position  # invert position for EnOcean
        self.__send_cover_command(
            command=EnOceanCoverCommand.SET_POSITION,
            destination=self.enocean_id,
            sender=self.sender_id,
            position=enocean_position,
        )

    def query_cover_position(self, entity_uid: EnOceanEntityUID) -> None:
        """Query the position of a cover device."""
        self.__send_cover_command(
            command=EnOceanCoverCommand.QUERY_POSITION_AND_ANGLE,
            destination=self.enocean_id,
            sender=self.sender_id,
        )

    def stop_cover(self, entity_uid: EnOceanEntityUID) -> None:
        """Stop the movement of a cover device."""
        self.__send_cover_command(
            command=EnOceanCoverCommand.STOP,
            destination=self.enocean_id,
            sender=self.sender_id,
        )

    def press_button(self, entity_uid: EnOceanEntityUID) -> None:
        """Simulate a button press."""
        if entity_uid == "query_state":
            print("Button press received to query cover state (position and angle).")
            self.query_cover_position(entity_uid)
