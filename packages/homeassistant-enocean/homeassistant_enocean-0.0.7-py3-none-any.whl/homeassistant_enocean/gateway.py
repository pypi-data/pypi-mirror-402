"""Representation of an EnOcean gateway."""

import logging
from .types import HomeAssistantTaskCreator, ValueLabelDict
from .serialcommunicator import EnOceanSerialCommunicator
from enocean.protocol.packet import Packet, RadioPacket
from enocean.utils import to_hex_string

from homeassistant_enocean.device_factories.a53808_factory import (
    EnOceanA53808DeviceFactory,
)
from homeassistant_enocean.devices.gateway_device import EnOceanGatewayDevice

from .device_factories.a502xx_factory import EnOceanA502XXDeviceFactory
from .device_factories.a504xx_factory import EnOceanA504XXDeviceFactory
from .device_factories.a50601_factory import EnOceanA50601DeviceFactory
from .device_factories.a50703_factory import EnOceanA50703DeviceFactory
from .device_factories.a50801_factory import EnOceanA50801DeviceFactory
from .device_factories.d201xx_factory import EnOceanD201XXDeviceFactory
from .device_factories.d20500_factory import EnOceanD20500DeviceFactory
from .device_factories.device_factory import EnOceanDeviceFactory
from .device_factories.f602xx_factory import EnOceanF602XXDeviceFactory

from homeassistant_enocean.eep import EEP
from homeassistant_enocean.entity_properties import HomeAssistantEntityProperties
from homeassistant_enocean.device_type import EnOceanDeviceType
from homeassistant_enocean.entity_id import EnOceanEntityID
from homeassistant_enocean.types import (
    EnOceanBinarySensorCallback,
    EnOceanCoverCallback,
    EnOceanEventCallback,
    EnOceanLightCallback,
    EnOceanSensorCallback,
    EnOceanSwitchCallback,
)
from .devices.device import EnOceanDevice
from .address import EnOceanAddress, EnOceanDeviceAddress

_LOGGER = logging.getLogger(__name__)


class EnOceanHomeAssistantGateway:
    """Representation of an EnOcean gateway for Home Assistant."""

    def __init__(self, serial_path: str, create_task: HomeAssistantTaskCreator) -> None:
        """Initialize the EnOcean gateway."""
        self.__communicator: EnOceanSerialCommunicator | None = None
        try:
            self.__communicator: EnOceanSerialCommunicator = EnOceanSerialCommunicator(
                port=serial_path
            )
            self.__communicator.teach_in = False
        except Exception as e:
            _LOGGER.error(f"Failed to initialize EnOceanSerialCommunicator: {e}")
            raise e

        self.__base_id: EnOceanAddress = EnOceanAddress(0)
        self.__chip_id: EnOceanAddress = EnOceanAddress(0)
        self.__chip_version: int = 0
        self.__sw_version: str = "n/a"
        self.__devices: dict[EnOceanDeviceAddress, EnOceanDevice] = {}
        self.__gateway_device: EnOceanGatewayDevice | None = None
        self.__create_task: HomeAssistantTaskCreator = create_task

        self.__device_factories: dict[EEP, EnOceanDeviceFactory] = {
            # A5-02 family
            EEP(0xA5, 0x02, 0x01): EnOceanA502XXDeviceFactory(),
            EEP(0xA5, 0x02, 0x02): EnOceanA502XXDeviceFactory(),
            EEP(0xA5, 0x02, 0x03): EnOceanA502XXDeviceFactory(),
            EEP(0xA5, 0x02, 0x04): EnOceanA502XXDeviceFactory(),
            EEP(0xA5, 0x02, 0x05): EnOceanA502XXDeviceFactory(),
            EEP(0xA5, 0x02, 0x06): EnOceanA502XXDeviceFactory(),
            EEP(0xA5, 0x02, 0x07): EnOceanA502XXDeviceFactory(),
            EEP(0xA5, 0x02, 0x08): EnOceanA502XXDeviceFactory(),
            EEP(0xA5, 0x02, 0x09): EnOceanA502XXDeviceFactory(),
            EEP(0xA5, 0x02, 0x0A): EnOceanA502XXDeviceFactory(),
            EEP(0xA5, 0x02, 0x0B): EnOceanA502XXDeviceFactory(),
            EEP(0xA5, 0x02, 0x10): EnOceanA502XXDeviceFactory(),
            EEP(0xA5, 0x02, 0x11): EnOceanA502XXDeviceFactory(),
            EEP(0xA5, 0x02, 0x12): EnOceanA502XXDeviceFactory(),
            EEP(0xA5, 0x02, 0x13): EnOceanA502XXDeviceFactory(),
            EEP(0xA5, 0x02, 0x14): EnOceanA502XXDeviceFactory(),
            EEP(0xA5, 0x02, 0x15): EnOceanA502XXDeviceFactory(),
            EEP(0xA5, 0x02, 0x16): EnOceanA502XXDeviceFactory(),
            EEP(0xA5, 0x02, 0x17): EnOceanA502XXDeviceFactory(),
            EEP(0xA5, 0x02, 0x18): EnOceanA502XXDeviceFactory(),
            EEP(0xA5, 0x02, 0x19): EnOceanA502XXDeviceFactory(),
            EEP(0xA5, 0x02, 0x1A): EnOceanA502XXDeviceFactory(),
            EEP(0xA5, 0x02, 0x1B): EnOceanA502XXDeviceFactory(),
            EEP(0xA5, 0x02, 0x20): EnOceanA502XXDeviceFactory(),
            EEP(0xA5, 0x02, 0x30): EnOceanA502XXDeviceFactory(),
            # A5-04 family
            EEP(0xA5, 0x04, 0x01): EnOceanA504XXDeviceFactory(),
            EEP(0xA5, 0x04, 0x02): EnOceanA504XXDeviceFactory(),
            EEP(0xA5, 0x04, 0x03): EnOceanA504XXDeviceFactory(),
            EEP(0xA5, 0x04, 0x04): EnOceanA504XXDeviceFactory(),
            # A5-06-01
            EEP(0xA5, 0x06, 0x01): EnOceanA50601DeviceFactory(),
            # A5-07-03
            EEP(0xA5, 0x07, 0x03): EnOceanA50703DeviceFactory(),
            # A5-08-01
            EEP(0xA5, 0x08, 0x01): EnOceanA50801DeviceFactory(),
            # A5-38-08
            EEP(0xA5, 0x38, 0x08): EnOceanA53808DeviceFactory(),
            # F6-02 family
            EEP(0xF6, 0x02, 0x01): EnOceanF602XXDeviceFactory(),
            EEP(0xF6, 0x02, 0x02): EnOceanF602XXDeviceFactory(),
            # D2-01 family
            EEP(0xD2, 0x01, 0x01): EnOceanD201XXDeviceFactory(),
            EEP(0xD2, 0x01, 0x02): EnOceanD201XXDeviceFactory(),
            EEP(0xD2, 0x01, 0x03): EnOceanD201XXDeviceFactory(),
            EEP(0xD2, 0x01, 0x04): EnOceanD201XXDeviceFactory(),
            EEP(0xD2, 0x01, 0x05): EnOceanD201XXDeviceFactory(),
            EEP(0xD2, 0x01, 0x06): EnOceanD201XXDeviceFactory(),
            EEP(0xD2, 0x01, 0x07): EnOceanD201XXDeviceFactory(),
            EEP(0xD2, 0x01, 0x08): EnOceanD201XXDeviceFactory(),
            EEP(0xD2, 0x01, 0x09): EnOceanD201XXDeviceFactory(),
            EEP(0xD2, 0x01, 0x0A): EnOceanD201XXDeviceFactory(),
            EEP(0xD2, 0x01, 0x0B): EnOceanD201XXDeviceFactory(),
            EEP(0xD2, 0x01, 0x0C): EnOceanD201XXDeviceFactory(),
            EEP(0xD2, 0x01, 0x0D): EnOceanD201XXDeviceFactory(),
            EEP(0xD2, 0x01, 0x0E): EnOceanD201XXDeviceFactory(),
            EEP(0xD2, 0x01, 0x0F): EnOceanD201XXDeviceFactory(),
            EEP(0xD2, 0x01, 0x10): EnOceanD201XXDeviceFactory(),
            EEP(0xD2, 0x01, 0x11): EnOceanD201XXDeviceFactory(),
            EEP(0xD2, 0x01, 0x12): EnOceanD201XXDeviceFactory(),
            EEP(0xD2, 0x01, 0x13): EnOceanD201XXDeviceFactory(),
            EEP(0xD2, 0x01, 0x14): EnOceanD201XXDeviceFactory(),
            EEP(0xD2, 0x05, 0x00): EnOceanD20500DeviceFactory(),
        }

    async def start(self) -> None:
        """Start the EnOcean gateway."""
        try:
            if not self.__communicator:
                raise RuntimeError("EnOcean SerialCommunicator is not initialized.")
            self.__communicator.start()
            self.__chip_id = EnOceanAddress(to_hex_string(self.__communicator.chip_id))
            self.__base_id = EnOceanAddress(to_hex_string(self.__communicator.base_id))
            self.__chip_version = self.__communicator.version_info.chip_version

            self.__sw_version = (
                self.__communicator.version_info.app_version.versionString()
                + " (App), "
                + self.__communicator.version_info.api_version.versionString()
                + " (API)"
            )
        except Exception as e:
            _LOGGER.error(f"Failed to start EnOcean SerialCommunicator: {e}")
            raise e

        # add the gateway device
        self.__gateway_device = EnOceanGatewayDevice(
            enocean_id=self.__chip_id,
            valid_sender_ids=self.valid_sender_ids,
            base_id=self.valid_sender_ids[1],
            create_task=self.__create_task,
        )
        self.__devices[self.__chip_id] = self.__gateway_device

        # callback needs to be set after initialization
        # in order for chip_id and base_id to be available
        self.__communicator.callback = self.__handle_packet

        for device in self.__devices.values():
            # set device's sender id to base id if not set
            if not device.sender_id:
                device.sender_id = self.__base_id

    def stop(self) -> None:
        """Stop the EnOcean gateway."""
        if self.__communicator:
            if self.__communicator.is_alive():
                self.__communicator.stop()

    def add_device(
        self,
        enocean_id: EnOceanDeviceAddress,
        device_type: EnOceanDeviceType,
        device_name: str | None = None,
        sender_id: EnOceanAddress | None = None,
    ) -> None:
        """Add a device to the gateway."""
        if enocean_id not in self.__devices:
            if device_type.eep not in self.__device_factories:
                print(
                    f'No EEP handler for EEP {device_type.eep} found, cannot add device "{device_name}" ({enocean_id.to_string()}).'
                )
                return

            factory = self.__device_factories[device_type.eep]
            device: EnOceanDevice = factory.create_device(
                enocean_id=enocean_id,
                device_type=device_type,
                send_packet=self._send_packet,
                device_name=device_name,
                sender_id=sender_id,
                create_task=self.__create_task,
            )
            self.__devices[enocean_id] = device

    def register_binary_sensor_callback(
        self, entity_id: EnOceanEntityID, callback: EnOceanBinarySensorCallback
    ) -> None:
        """Register a callback for a binary sensor entity."""
        self.__devices[entity_id.device_address]._binary_sensor_callbacks[
            entity_id.unique_id
        ] = callback

    def register_cover_callback(
        self, entity_id: EnOceanEntityID, callback: EnOceanCoverCallback
    ) -> None:
        """Register a callback for a cover entity."""
        self.__devices[entity_id.device_address]._cover_callbacks[
            entity_id.unique_id
        ] = callback

    def register_event_callback(
        self, entity_id: EnOceanEntityID, callback: EnOceanEventCallback
    ) -> None:
        """Register a callback for an event entity."""
        self.__devices[entity_id.device_address]._event_callbacks[
            entity_id.unique_id
        ] = callback

    def register_sensor_callback(
        self, entity_id: EnOceanEntityID, callback: EnOceanSensorCallback
    ) -> None:
        """Register a callback for a sensor entity."""
        self.__devices[entity_id.device_address]._sensor_callbacks[
            entity_id.unique_id
        ] = callback

    def register_switch_callback(
        self, entity_id: EnOceanEntityID, callback: EnOceanSwitchCallback
    ) -> None:
        """Register a callback for a switch entity."""
        self.__devices[entity_id.device_address]._switch_callbacks[
            entity_id.unique_id
        ] = callback

    def register_light_callback(
        self, entity_id: EnOceanEntityID, callback: EnOceanLightCallback
    ) -> None:
        """Register a callback for a light entity."""
        self.__devices[entity_id.device_address]._light_callbacks[
            entity_id.unique_id
        ] = callback

    @property
    def base_id(self) -> EnOceanAddress:
        """Returns the gateway's base id."""
        return self.__base_id

    @property
    def chip_id(self) -> EnOceanAddress:
        """Returns the gateway's chip id."""
        return self.__chip_id

    @property
    def valid_sender_ids(self) -> list[ValueLabelDict]:
        """Returns a list of valid sender ids."""

        if not self.__base_id or not self.__chip_id:
            return []

        valid_senders = [
            ValueLabelDict(
                value=self.__chip_id.to_string(),
                label="Chip ID (" + self.__chip_id.to_string() + ")",
            ),
            ValueLabelDict(
                value=self.__base_id.to_string(),
                label="Base ID (" + self.__base_id.to_string() + ")",
            ),
        ]
        base_id_int = self.__base_id.to_number()
        valid_senders.extend(
            [
                ValueLabelDict(
                    value=EnOceanAddress(base_id_int + i).to_string(),
                    label="Base ID + "
                    + "{:03d}".format(i)
                    + " ("
                    + EnOceanAddress(base_id_int + i).to_string()
                    + ")",
                )
                for i in range(1, 128)
            ]
        )

        return valid_senders

    @property
    def chip_version(self) -> int:
        """Get the gateway's chip version."""
        return self.__chip_version

    @property
    def sw_version(self) -> str:
        """Get the gateway's software version."""
        return self.__sw_version

    def get_device_properties(self, enocean_id: EnOceanAddress) -> EnOceanDevice | None:
        """Return the device properties for a given EnOcean ID."""
        return self.__devices.get(enocean_id)

    def _send_packet(self, packet: Packet) -> None:
        """Send a packet through the EnOcean gateway."""
        self.__communicator.send(packet)

    def __handle_packet(self, packet: Packet) -> None:
        """Handle incoming EnOcean packet."""
        if not isinstance(packet, RadioPacket):
            return

        # in learning mode, let the gateway device handle the packet
        if self.__gateway_device and self.__gateway_device.is_learning:
            if new_device := self.__gateway_device.teach(packet, self._send_packet):
                print(f"Learned new device with address {new_device.to_string()}.")
                # self.add_device()
                return

        # else, find the device corresponding to the sender address
        if device := self.__devices.get(EnOceanAddress(packet.sender_hex)):
            device.handle_packet(packet)

    # Entity listings
    @property
    def binary_sensor_entities(
        self,
    ) -> list[EnOceanEntityID, HomeAssistantEntityProperties]:
        """Return the list of binary sensor entities."""
        entities = {}

        # iterate over all devices and get their binary sensor entities
        for device in self.__devices.values():
            for entity in device.binary_sensor_entities:
                entity_id = EnOceanEntityID(
                    device_address=device.enocean_id,
                    unique_id=entity.unique_id,
                )
                entities[entity_id] = entity

        return entities

    @property
    def button_entities(self) -> list[EnOceanEntityID, HomeAssistantEntityProperties]:
        """Return the list of button entities."""
        entities = {}

        # iterate over all devices and get their button entities
        for device in self.__devices.values():
            for entity in device.button_entities:
                entity_id = EnOceanEntityID(
                    device_address=device.enocean_id,
                    unique_id=entity.unique_id,
                )
                entities[entity_id] = entity

        return entities

    @property
    def cover_entities(self) -> list[EnOceanEntityID, HomeAssistantEntityProperties]:
        """Return the list of cover entities."""
        entities = {}

        # iterate over all devices and get their cover entities
        for device in self.__devices.values():
            for entity in device.cover_entities:
                entity_id = EnOceanEntityID(
                    device_address=device.enocean_id,
                    unique_id=entity.unique_id,
                )
                entities[entity_id] = entity

        return entities

    @property
    def number_entities(self) -> list[EnOceanEntityID, HomeAssistantEntityProperties]:
        """Return the list of number entities."""
        entities = {}

        # iterate over all devices and get their number entities
        for device in self.__devices.values():
            for entity in device.number_entities:
                entity_id = EnOceanEntityID(
                    device_address=device.enocean_id,
                    unique_id=entity.unique_id,
                )
                entities[entity_id] = entity

        return entities

    @property
    def select_entities(self) -> list[EnOceanEntityID, HomeAssistantEntityProperties]:
        """Return the list of select entities."""
        entities = {}
        # iterate over all devices and get their select entities
        for device in self.__devices.values():
            for entity in device.select_entities:
                entity_id = EnOceanEntityID(
                    device_address=device.enocean_id,
                    unique_id=entity.unique_id,
                )
                entities[entity_id] = entity

        return entities

    @property
    def sensor_entities(self) -> list[EnOceanEntityID, HomeAssistantEntityProperties]:
        """Return the list of sensor entities."""
        entities = {}
        # iterate over all devices and get their sensor entities
        for device in self.__devices.values():
            for entity in device.sensor_entities:
                entity_id = EnOceanEntityID(
                    device_address=device.enocean_id,
                    unique_id=entity.unique_id,
                )
                entities[entity_id] = entity

        return entities

    @property
    def switch_entities(self) -> list[EnOceanEntityID, HomeAssistantEntityProperties]:
        """Return the list of switch entities."""
        entities = {}

        # iterate over all devices and get their switch entities
        for device in self.__devices.values():
            for entity in device.switch_entities:
                entity_id = EnOceanEntityID(
                    device_address=device.enocean_id,
                    unique_id=entity.unique_id,
                )
                entities[entity_id] = entity

        return entities

    @property
    def light_entities(self) -> list[EnOceanEntityID, HomeAssistantEntityProperties]:
        """Return the list of light entities."""
        entities = {}

        # iterate over all devices and get their light entities
        for device in self.__devices.values():
            for entity in device.light_entities:
                entity_id = EnOceanEntityID(
                    device_address=device.enocean_id,
                    unique_id=entity.unique_id,
                )
                entities[entity_id] = entity

        return entities

    # button commands
    def press_button(self, enocean_entity_id: EnOceanEntityID) -> None:
        """Press a button entity."""
        if device := self.__devices.get(enocean_entity_id.device_address):
            device.press_button(entity_uid=enocean_entity_id.unique_id)

    # cover commands
    def set_cover_position(
        self, enocean_entity_id: EnOceanEntityID, position: int
    ) -> None:
        """Set the position of a cover device (0 = closed, 100 = open)."""
        if device := self.__devices.get(enocean_entity_id.device_address):
            device.set_cover_position(
                entity_uid=enocean_entity_id.unique_id, position=position
            )

    def query_cover_position(self, enocean_entity_id: EnOceanEntityID) -> None:
        """Query the position of a cover device."""
        if device := self.__devices.get(enocean_entity_id.device_address):
            device.query_cover_position(entity_uid=enocean_entity_id.unique_id)

    def stop_cover(self, enocean_entity_id: EnOceanEntityID) -> None:
        """Stop a cover device."""
        if device := self.__devices.get(enocean_entity_id.device_address):
            device.stop_cover(entity_uid=enocean_entity_id.unique_id)

    # number commands
    def set_number_value(
        self, enocean_entity_id: EnOceanEntityID, value: float
    ) -> None:
        """Set the value of a number entity."""
        if device := self.__devices.get(enocean_entity_id.device_address):
            device.set_number_value(entity_uid=enocean_entity_id.unique_id, value=value)

    # light commands
    def light_turn_on(
        self,
        enocean_entity_id: EnOceanEntityID,
        brightness: int | None = None,
        color_temp_kelvin: int | None = None,
    ) -> None:
        """Turn on a light device."""
        if device := self.__devices.get(enocean_entity_id.device_address):
            device.light_turn_on(
                entity_uid=enocean_entity_id.unique_id,
                brightness=brightness,
                color_temp_kelvin=color_temp_kelvin,
            )

    def light_turn_off(self, enocean_entity_id: EnOceanEntityID) -> None:
        """Turn off a light device."""
        if device := self.__devices.get(enocean_entity_id.device_address):
            device.light_turn_off(entity_uid=enocean_entity_id.unique_id)

    # select commands
    def select_option(self, enocean_entity_id: EnOceanEntityID, option: str) -> None:
        """Set the option of a select entity."""
        if device := self.__devices.get(enocean_entity_id.device_address):
            device.select_option(entity_uid=enocean_entity_id.unique_id, option=option)

    # switch commands
    def switch_turn_on(self, enocean_entity_id: EnOceanEntityID) -> None:
        """Turn on a switch device."""
        if device := self.__devices.get(enocean_entity_id.device_address):
            device.switch_turn_on(entity_uid=enocean_entity_id.unique_id)

    def switch_turn_off(self, enocean_entity_id: EnOceanEntityID) -> None:
        """Turn off a switch device."""
        if device := self.__devices.get(enocean_entity_id.device_address):
            device.switch_turn_off(entity_uid=enocean_entity_id.unique_id)
