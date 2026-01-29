from ..address import EnOceanAddress, EnOceanDeviceAddress
from .device_factory import EnOceanDeviceFactory
from ..device_type import EnOceanDeviceType
from ..devices.a504xx_device import EnOceanA504XXDevice
from ..eep import EEP
from ..types import EnOceanSendRadioPacket, HomeAssistantTaskCreator


class EnOceanA504XXDeviceFactory(EnOceanDeviceFactory):
    """Factory class to create EnOcean A5-02-XX devices based on EEP."""

    def create_device(
        self,
        enocean_id: EnOceanDeviceAddress,
        device_type: EnOceanDeviceType,
        send_packet: EnOceanSendRadioPacket | None = None,
        device_name: str | None = None,
        sender_id: EnOceanAddress = None,
        create_task: HomeAssistantTaskCreator | None = None,
    ) -> EnOceanA504XXDevice:
        """Create an EnOcean A504XX device based on the provided EEP."""

        supported_eeps = [
            EEP(0xA5, 0x04, 0x01),
            EEP(0xA5, 0x04, 0x02),
            EEP(0xA5, 0x04, 0x03),
            EEP(0xA5, 0x04, 0x04),
        ]

        if device_type.eep in supported_eeps:
            return EnOceanA504XXDevice(
                enocean_id=enocean_id,
                device_type=device_type,
                create_task=create_task,
                send_packet=send_packet,
                device_name=device_name,
                sender_id=sender_id,
            )
        else:
            raise ValueError(
                f"EEP {device_type.eep} is not supported by EnOceanA504XXDeviceFactory."
            )
