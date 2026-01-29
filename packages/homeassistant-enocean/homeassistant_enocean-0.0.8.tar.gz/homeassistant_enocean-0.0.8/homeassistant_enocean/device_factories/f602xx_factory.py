from ..address import EnOceanAddress, EnOceanDeviceAddress
from ..device_factories.device_factory import EnOceanDeviceFactory
from ..device_type import EnOceanDeviceType
from ..devices.f602xx_device import EnOceanF602XXDevice
from ..eep import EEP
from ..types import EnOceanSendRadioPacket, HomeAssistantTaskCreator


class EnOceanF602XXDeviceFactory(EnOceanDeviceFactory):
    """Factory class to create EnOcean F602XX devices based on EEP."""

    def create_device(
        self,
        enocean_id: EnOceanDeviceAddress,
        device_type: EnOceanDeviceType,
        send_packet: EnOceanSendRadioPacket | None = None,
        device_name: str | None = None,
        sender_id: EnOceanAddress = None,
        create_task: HomeAssistantTaskCreator | None = None,
    ) -> EnOceanF602XXDevice:
        """Create an EnOcean F602XX device based on the provided EEP."""

        if device_type.eep == EEP(0xF6, 0x02, 0x01) or device_type.eep == EEP(
            0xF6, 0x02, 0x02
        ):
            return EnOceanF602XXDevice(
                enocean_id=enocean_id,
                device_type=device_type,
                create_task=create_task,
                send_packet=send_packet,
                device_name=device_name,
                sender_id=sender_id,
            )
        else:
            raise ValueError(
                f"EEP {device_type.eep} is not supported by EnOceanF602XXDeviceFactory."
            )
