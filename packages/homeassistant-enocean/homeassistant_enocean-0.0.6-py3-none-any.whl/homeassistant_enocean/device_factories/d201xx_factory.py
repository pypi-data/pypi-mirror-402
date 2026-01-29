from ..types import EnOceanSendRadioPacket, HomeAssistantTaskCreator
from ..address import EnOceanAddress, EnOceanDeviceAddress
from .device_factory import EnOceanDeviceFactory
from ..device_type import EnOceanDeviceType
from ..devices.d201xx_device import EnOceanD201XXDevice
from ..eep import EEP


class EnOceanD201XXDeviceFactory(EnOceanDeviceFactory):
    """Factory class to create EnOcean D2-01-XX devices based on EEP."""

    def create_device(
        self,
        enocean_id: EnOceanDeviceAddress,
        device_type: EnOceanDeviceType,
        send_packet: EnOceanSendRadioPacket | None = None,
        device_name: str | None = None,
        sender_id: EnOceanAddress = None,
        create_task: HomeAssistantTaskCreator | None = None,
    ) -> EnOceanD201XXDevice:
        """Create an EnOcean D201XX device based on the provided EEP."""

        supported_eeps = [
            EEP(0xD2, 0x01, 0x01),
            EEP(0xD2, 0x01, 0x02),
            EEP(0xD2, 0x01, 0x03),
            EEP(0xD2, 0x01, 0x04),
            EEP(0xD2, 0x01, 0x05),
            EEP(0xD2, 0x01, 0x06),
            EEP(0xD2, 0x01, 0x07),
            EEP(0xD2, 0x01, 0x08),
            EEP(0xD2, 0x01, 0x09),
            EEP(0xD2, 0x01, 0x0A),
            EEP(0xD2, 0x01, 0x0B),
            EEP(0xD2, 0x01, 0x0C),
            EEP(0xD2, 0x01, 0x0D),
            EEP(0xD2, 0x01, 0x0E),
            EEP(0xD2, 0x01, 0x0F),
            EEP(0xD2, 0x01, 0x10),
            EEP(0xD2, 0x01, 0x11),
            EEP(0xD2, 0x01, 0x12),
            EEP(0xD2, 0x01, 0x13),
            EEP(0xD2, 0x01, 0x14),
        ]

        if device_type.eep in supported_eeps:
            return EnOceanD201XXDevice(
                enocean_id=enocean_id,
                device_type=device_type,
                create_task=create_task,
                send_packet=send_packet,
                device_name=device_name,
                sender_id=sender_id,
            )
        else:
            raise ValueError(
                f"EEP {device_type.eep} is not supported by EnOceanD201XXDeviceFactory."
            )
