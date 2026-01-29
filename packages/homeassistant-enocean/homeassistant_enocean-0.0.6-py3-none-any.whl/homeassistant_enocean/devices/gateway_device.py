import asyncio
from typing import Callable
from ..address import EnOceanAddress
from ..device_type import EnOceanDeviceType
from ..devices.device import EnOceanDevice
from ..eep import EEP
from ..entity_properties import HomeAssistantEntityProperties
from ..types import EnOceanEntityUID, HomeAssistantTaskCreator, ValueLabelDict
from enocean.protocol.packet import RadioPacket, UTETeachInPacket


class EnOceanGatewayDevice(EnOceanDevice):
    LEARNING_TIMEOUT: int = 60

    """EnOcean Gateway Device"""

    def __init__(
        self,
        enocean_id,
        valid_sender_ids: list[ValueLabelDict] | None = None,
        base_id: ValueLabelDict | None = None,
        create_task: HomeAssistantTaskCreator | None = None,
    ) -> None:
        """Initialize the EnOcean Gateway Device."""
        self._valid_sender_ids = valid_sender_ids
        self.__learning_mode_active = False
        self.__base_id = base_id

        self.__learning_id: EnOceanAddress | None = None
        self.__learning_countdown = 5

        super().__init__(
            enocean_id=enocean_id,
            send_packet=None,
            device_type=EnOceanDeviceType(
                eep=EEP(0, 0, 0), model="TCM300/310 Transmitter", manufacturer="EnOcean"
            ),
            device_name="EnOcean Gateway",
            sender_id=None,
            create_task=create_task,
        )

    def initialize_entities(self) -> None:
        """Initialize the entities handled by this EEP handler."""
        self.clear_internal_sensor_entities()
        self._button_entities = [
            HomeAssistantEntityProperties(
                unique_id="toggle_learning", entity_category="diagnostic"
            ),
        ]

        valid_sender_ids = []
        if self._valid_sender_ids:
            valid_sender_ids = [option["label"] for option in self._valid_sender_ids]

        self.__learning_id = (
            EnOceanAddress(self.__base_id["value"]) if self.__base_id else None
        )

        self._binary_sensor_entities = [
            HomeAssistantEntityProperties(
                unique_id="learning", entity_category="diagnostic"
            ),
        ]

        self._select_entities = [
            HomeAssistantEntityProperties(
                unique_id="sender_id",
                entity_category="diagnostic",
                options=valid_sender_ids,
                current_option=self.__base_id["label"] if self.__base_id else None,
            ),
        ]

        self._sensor_entities = [
            HomeAssistantEntityProperties(
                unique_id="learning_countdown",
                device_class="duration",
                native_unit_of_measurement="s",
                entity_category="diagnostic",
            ),
        ]

        if learning_callback := self._binary_sensor_callbacks.get("learning"):
            learning_callback(self.__learning_mode_active)

    def handle_matching_packet(self, packet) -> None:
        """Handle an incoming EnOcean packet."""
        return

    def teach(
        self, packet: RadioPacket, send: Callable[[RadioPacket], None]
    ) -> EnOceanAddress | None:
        """Inspect an incoming EnOcean packet without processing it."""
        # Gateway device handles learning
        # in learning mode, only respond to UTE Teach-In packets and ignore all other packets
        if self.__learning_mode_active and self.__learning_id:
            # UTE teach-in
            if isinstance(packet, UTETeachInPacket):
                device_address = EnOceanAddress(packet.sender_hex)
                device_eep = EEP(
                    rorg=packet.rorg_of_eep,
                    func=packet.rorg_func,
                    type_=packet.rorg_type,
                )
                print(
                    f"Received UTE Teach-In packet from {device_address.to_string()} with EEP {device_eep.to_string()}."
                )
                response = packet.create_response_packet(
                    self.__learning_id.to_bytelist()
                )
                print(
                    f"Responding with UTE Teach-In response packet to {device_address.to_string()} using sender id {self.__learning_id.to_string()}."
                )
                send(response)
                self.stop_learning()
                return device_address

            if not isinstance(packet, RadioPacket):
                return

            # 4BS teach in
            if packet.rorg == 0xF6 and packet.learn:
                print(
                    "UNSUPPORTED: Received 4BS Teach-In packet from "
                    + EnOceanAddress(packet.sender_hex).to_string()
                    + "."
                )
                self.stop_learning()
                return

    def press_button(self, entity_uid: EnOceanEntityUID) -> None:
        """Handle button press actions."""
        if entity_uid == "toggle_learning":
            self.__learning_mode_active = not self.__learning_mode_active

            if self.__learning_mode_active:
                self.__learning_countdown = self.LEARNING_TIMEOUT
                if learning_countdown_callback := self._sensor_callbacks.get(
                    "learning_countdown"
                ):
                    learning_countdown_callback(self.__learning_countdown)
                if self.create_task:
                    self.create_task(target=self._learning_timeout())

            if learning_callback := self._binary_sensor_callbacks.get("learning"):
                learning_callback(self.__learning_mode_active)

    def select_option(self, entity_uid: EnOceanEntityUID, option: str) -> None:
        """Handle select option actions."""
        if entity_uid == "sender_id":
            if self._valid_sender_ids:
                for option_dict in self._valid_sender_ids:
                    if option_dict["label"] == option:
                        self.__learning_id = EnOceanAddress(option_dict["value"])
                        print(
                            f"Gateway learning ID set to {self.__learning_id.to_string()}."
                        )
                        break

    def stop_learning(self) -> None:
        """Stop learning mode."""
        self.__learning_mode_active = False
        if learning_callback := self._binary_sensor_callbacks.get("learning"):
            learning_callback(self.__learning_mode_active)

    async def _learning_timeout(self) -> None:
        """Handle learning mode timeout."""
        learning_countdown_callback = self._sensor_callbacks.get("learning_countdown")

        while 1:
            await asyncio.sleep(1)

            if not self.__learning_mode_active:
                if learning_countdown_callback:
                    learning_countdown_callback(0)
                return

            self.__learning_countdown -= 1

            if learning_countdown_callback:
                learning_countdown_callback(self.__learning_countdown)

            if self.__learning_countdown <= 0:
                self.stop_learning()
                return

    @property
    def is_learning(self) -> bool:
        return self.__learning_mode_active
