"""Representation of an EnOcean device state."""

import datetime
from typing import Any, Coroutine
from ..entity_properties import HomeAssistantEntityProperties
from ..types import (
    EnOceanBinarySensorCallback,
    EnOceanCoverCallback,
    EnOceanEntityUID,
    EnOceanEventCallback,
    EnOceanLightCallback,
    EnOceanSendRadioPacket,
    EnOceanSensorCallback,
    EnOceanSwitchCallback,
    HomeAssistantTaskCreator,
)
from ..device_type import EnOceanDeviceType
from ..address import EnOceanAddress, EnOceanDeviceAddress
from abc import abstractmethod, ABC
from enocean.protocol.packet import RadioPacket, UTETeachInPacket


class EnOceanDevice(ABC):
    """Representation of an EnOcean device."""

    def __init__(
        self,
        enocean_id: EnOceanDeviceAddress,
        device_type: EnOceanDeviceType,
        create_task: HomeAssistantTaskCreator | None = None,
        send_packet: EnOceanSendRadioPacket | None = None,
        device_name: str | None = None,
        sender_id: EnOceanAddress | None = None,
    ) -> None:
        """Construct an EnOcean device."""
        self.__enocean_id = enocean_id
        self.__device_type = device_type
        self.__ha_create_task = create_task
        self.device_name = device_name
        self.__sender_id = sender_id

        self.__send_packet = send_packet
        self.__telegrams_received = 0

        # callbacks
        self._binary_sensor_callbacks: dict[
            EnOceanEntityUID, EnOceanBinarySensorCallback
        ] = {}
        self._cover_callbacks: dict[EnOceanEntityUID, EnOceanCoverCallback] = {}
        self._event_callbacks: dict[EnOceanEntityUID, EnOceanEventCallback] = {}
        self._light_callbacks: dict[EnOceanEntityUID, EnOceanLightCallback] = {}
        self._sensor_callbacks: dict[EnOceanEntityUID, EnOceanSensorCallback] = {}
        self._switch_callbacks: dict[EnOceanEntityUID, EnOceanSwitchCallback] = {}

        # entities
        self._binary_sensor_entities: list[HomeAssistantEntityProperties] = []
        self._button_entities: list[HomeAssistantEntityProperties] = []
        self._cover_entities: list[HomeAssistantEntityProperties] = []
        self._light_entities: list[HomeAssistantEntityProperties] = []
        self._number_entities: list[HomeAssistantEntityProperties] = []
        self.__internal_sensor_entities: list[HomeAssistantEntityProperties] = [
            HomeAssistantEntityProperties(
                unique_id="rssi",
                native_unit_of_measurement="dBm",
                device_class="signal_strength",
                entity_category="diagnostic",
            ),
            HomeAssistantEntityProperties(
                unique_id="telegrams_received",
                sensor_state_class="total_increasing",
                entity_category="diagnostic",
                last_reset=datetime.datetime.now().astimezone(),
            ),
            HomeAssistantEntityProperties(
                unique_id="last_seen",
                device_class="timestamp",
                entity_category="diagnostic",
            ),
        ]
        self._select_entities: list[HomeAssistantEntityProperties] = []
        self._sensor_entities: list[HomeAssistantEntityProperties] = []
        self._switch_entities: list[HomeAssistantEntityProperties] = []
        self.initialize_entities()

    def clear_internal_sensor_entities(self) -> None:
        """Clear internal sensor entities (used for the gateway device)."""
        self.__internal_sensor_entities.clear()

    @property
    def enocean_id(self) -> EnOceanDeviceAddress:
        """Return the device ID."""
        return self.__enocean_id

    @property
    def device_type(self) -> EnOceanDeviceType:
        """Return the device type."""
        return self.__device_type

    @property
    def sender_id(self) -> EnOceanAddress | None:
        """Return the sender ID."""
        return self.__sender_id

    @sender_id.setter
    def sender_id(self, value: EnOceanAddress | None) -> None:
        """Set the sender ID."""
        self.__sender_id = value

    @property
    def binary_sensor_entities(self) -> list[HomeAssistantEntityProperties]:
        """Return the binary sensor entities."""
        return self._binary_sensor_entities

    @property
    def button_entities(self) -> list[HomeAssistantEntityProperties]:
        """Return the button entities."""
        return self._button_entities

    @property
    def cover_entities(self) -> list[HomeAssistantEntityProperties]:
        """Return the cover entities."""
        return self._cover_entities

    @property
    def event_entities(self) -> list[HomeAssistantEntityProperties]:
        """Return the event entities."""
        return []

    @property
    def light_entities(self) -> list[HomeAssistantEntityProperties]:
        """Return the light entities."""
        return self._light_entities

    @property
    def number_entities(self) -> list[HomeAssistantEntityProperties]:
        """Return the number entities."""
        return self._number_entities

    @property
    def select_entities(self) -> list[HomeAssistantEntityProperties]:
        """Return the select entities."""
        return self._select_entities

    @property
    def sensor_entities(self) -> list[HomeAssistantEntityProperties]:
        """Return the sensor entities."""
        return self._sensor_entities + self.__internal_sensor_entities

    @property
    def switch_entities(self) -> list[HomeAssistantEntityProperties]:
        """Return the switch entities."""
        return self._switch_entities

    def create_task(self, target: Coroutine[Any, Any, Any]) -> None:
        """Create a Home Assistant task."""
        self.__ha_create_task(target=target)

    def handle_packet(self, packet: RadioPacket) -> None:
        """Handle an incoming EnOcean packet; this will ignore UTE packets."""
        # print(f"EEPHandler.handle_packet: Checking packet from sender {EnOceanAddress.from_number(packet.sender_int)} against device ID {enocean_id.to_string()}")

        if isinstance(packet, UTETeachInPacket):
            return

        if packet.sender_int == self.enocean_id.to_number():
            rssi_callback = self._sensor_callbacks.get("rssi")
            if rssi_callback:
                rssi_callback(packet.dBm)

            self.__telegrams_received += 1
            telegram_seen_callback = self._sensor_callbacks.get("telegrams_received")
            if telegram_seen_callback:
                telegram_seen_callback(self.__telegrams_received)

            last_seen_callback = self._sensor_callbacks.get("last_seen")
            if last_seen_callback:
                last_seen_callback(datetime.datetime.now().astimezone())

            self.handle_matching_packet(packet)

    def send_packet(self, packet: RadioPacket) -> None:
        """Send an EnOcean packet."""
        if self.__send_packet:
            self.__send_packet(packet)

    @abstractmethod
    def initialize_entities(self) -> None:
        """Initialize the entities handled by this EEP handler."""
        pass

    @abstractmethod
    def handle_matching_packet(self, packet: RadioPacket) -> None:
        """Handle an incoming EnOcean packet."""
        pass

    # button-specific methods
    def press_button(self, entity_uid: EnOceanEntityUID) -> None:
        """Simulate a button press."""
        pass

    # cover-specific methods
    def set_cover_position(self, entity_uid: EnOceanEntityUID, position: int) -> None:
        """Set the position of a cover device (0 = closed, 100 = open)."""
        pass

    def query_cover_position(self, entity_uid: EnOceanEntityUID) -> None:
        """Query the position of a cover device."""
        pass

    def stop_cover(self, entity_uid: EnOceanEntityUID) -> None:
        """Stop the movement of a cover device."""
        pass

    # number-specific methods
    def set_number_value(self, entity_uid: EnOceanEntityUID, value: float) -> None:
        """Set the value of a number entity."""
        pass

    # light-specific methods
    def light_turn_on(
        self,
        entity_uid: EnOceanEntityUID,
        brightness: int | None = None,
        color_temp_kelvin: int | None = None,
    ) -> None:
        """Turn on a light device."""
        pass

    def light_turn_off(self, entity_uid: EnOceanEntityUID) -> None:
        """Turn off a light device."""
        pass

    # select-specific methods
    def select_option(self, entity_uid: EnOceanEntityUID, option: str) -> None:
        """Set the option of a select entity."""
        pass

    # switch-specific methods
    def switch_turn_on(self, entity_uid: EnOceanEntityUID) -> None:
        """Turn on a switch device."""
        pass

    def switch_turn_off(self, entity_uid: EnOceanEntityUID) -> None:
        """Turn off a switch device."""
        pass
