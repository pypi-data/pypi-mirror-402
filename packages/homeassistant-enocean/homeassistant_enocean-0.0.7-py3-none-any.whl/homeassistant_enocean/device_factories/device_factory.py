from abc import ABC, abstractmethod

from ..types import EnOceanSendRadioPacket, HomeAssistantTaskCreator
from ..device_type import EnOceanDeviceType
from ..address import EnOceanAddress, EnOceanDeviceAddress
from ..devices.device import EnOceanDevice


class EnOceanDeviceFactory(ABC):
    """Factory class to create EnOcean devices based on EEP."""

    @abstractmethod
    def create_device(
        self,
        enocean_id: EnOceanDeviceAddress,
        device_type: EnOceanDeviceType,
        send_packet: EnOceanSendRadioPacket | None = None,
        device_name: str | None = None,
        sender_id: EnOceanAddress = None,
        create_task: HomeAssistantTaskCreator | None = None,
    ) -> EnOceanDevice:
        """Create an EnOcean device based on the provided EEP."""
        pass
