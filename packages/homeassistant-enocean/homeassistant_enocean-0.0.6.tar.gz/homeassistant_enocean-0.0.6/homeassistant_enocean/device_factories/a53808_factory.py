from ..address import EnOceanAddress, EnOceanDeviceAddress
from .device_factory import EnOceanDeviceFactory
from ..device_type import EnOceanDeviceType
from ..devices.a53808_device import EnOceanA53808Device
from ..eep import EEP
from ..types import EnOceanSendRadioPacket, HomeAssistantTaskCreator


class EnOceanA53808DeviceFactory(EnOceanDeviceFactory):
    """Factory class to create EnOcean A5-38-08 devices based on EEP."""

    def create_device(
        self,
        enocean_id: EnOceanDeviceAddress,
        device_type: EnOceanDeviceType,
        send_packet: EnOceanSendRadioPacket | None = None,
        device_name: str | None = None,
        sender_id: EnOceanAddress = None,
        create_task: HomeAssistantTaskCreator | None = None,
    ) -> EnOceanA53808Device:
        """Create an EnOcean A53808 device based on the provided EEP."""

        if device_type.eep == EEP(0xA5, 0x38, 0x08):
            return EnOceanA53808Device(
                enocean_id=enocean_id,
                device_type=device_type,
                create_task=create_task,
                send_packet=send_packet,
                device_name=device_name,
                sender_id=sender_id,
            )
        else:
            raise ValueError(
                f"EEP {device_type.eep} is not supported by EnOceanA53808DeviceFactory."
            )
