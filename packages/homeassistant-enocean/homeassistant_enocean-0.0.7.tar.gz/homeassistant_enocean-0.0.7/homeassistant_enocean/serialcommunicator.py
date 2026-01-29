from enocean.communicators.serialcommunicator import SerialCommunicator
import datetime
import logging
import queue
from enocean.protocol.constants import PACKET, RETURN_CODE
from enocean.protocol.packet import Packet
from .types import VersionInfo, COMMON_COMMAND

LOGGER = logging.getLogger("enocean.communicators.SerialCommunicator")


class EnOceanSerialCommunicator(SerialCommunicator):
    """Extends the original 'SerialCommunicator' class to provide version info fetching functionality (incl. chip ID)."""

    def __init__(self, port: str = "/dev/ttyAMA0") -> None:
        super().__init__(port=port)
        self._version_info: VersionInfo | None = None

    @property
    def base_id(self):
        """Fetches Base ID from the transmitter, if required. Otherwise, returns the currently set Base ID."""
        # If base id is already set, return it.
        if self._base_id is not None:
            return self._base_id

        start = datetime.datetime.now()

        # Send COMMON_COMMAND 0x08, CO_RD_IDBASE request to the module
        self.send(
            Packet(
                PACKET.COMMON_COMMAND,
                data=[COMMON_COMMAND.CO_RD_IDBASE.value],
                optional=[],
            )
        )

        # wait at most 1 second for the response
        while True:
            seconds_elapsed = (datetime.datetime.now() - start).total_seconds()
            if seconds_elapsed > 1:
                self.logger.error(
                    "Could not obtain base id from module within 1 second (timeout)."
                )
                break
            try:
                packet = self.receive.get(block=True, timeout=0.1)
                # We're only interested in responses to the request in question.
                if (
                    packet.packet_type == PACKET.RESPONSE
                    and packet.response == RETURN_CODE.OK
                    and len(packet.response_data) == 4
                ):
                    # Base ID is set in the response data.
                    self._base_id = packet.response_data
                    # Put packet back to the Queue, so the user can also react to it if required...
                    self.receive.put(packet)
                    break
                # Put other packets back to the Queue.
                self.receive.put(packet)
            except queue.Empty:
                continue
        # Return the current Base ID (might be None).
        return self._base_id

    @property
    def chip_id(self):
        """Fetches Chip ID from the transmitter, if required. Otherwise returns the currently set Chip ID."""
        if self.version_info is not None:
            return self.version_info.chip_id

        return None

    @property
    def version_info(self):
        """Fetches version info from the transmitter, if required. Otherwise returns the currently set version info."""

        # If version info is already set, return it.
        if self._version_info is not None:
            return self._version_info

        start = datetime.datetime.now()

        # Send COMMON_COMMAND 0x03, CO_RD_VERSION request to the module
        self.send(
            Packet(
                PACKET.COMMON_COMMAND,
                data=[COMMON_COMMAND.CO_RD_VERSION.value],
                optional=[],
            )
        )

        # wait at most 1 second for the response
        while True:
            seconds_elapsed = (datetime.datetime.now() - start).total_seconds()
            if seconds_elapsed > 1:
                LOGGER.warning(
                    "Could not obtain version info from module within 1 second (timeout)."
                )
                break

            try:
                packet = self.receive.get(block=True, timeout=0.1)
                if (
                    packet.packet_type == PACKET.RESPONSE
                    and packet.response == RETURN_CODE.OK
                    and len(packet.response_data) == 32
                ):
                    # interpret the version info
                    self._version_info: VersionInfo = VersionInfo()
                    res = packet.response_data

                    self._version_info.app_version.main = res[0]
                    self._version_info.app_version.beta = res[1]
                    self._version_info.app_version.alpha = res[2]
                    self._version_info.app_version.build = res[3]

                    self._version_info.api_version.main = res[4]
                    self._version_info.api_version.beta = res[5]
                    self._version_info.api_version.alpha = res[6]
                    self._version_info.api_version.build = res[7]

                    self._version_info.chip_id = [res[8], res[9], res[10], res[11]]
                    self._version_info.chip_version = int.from_bytes(res[12:15], "big")

                    self._version_info.app_description = (
                        bytearray(res[16:32]).decode("utf8").strip().split("\x00")[0]
                    )

                    # Put packet back to the Queue, so the user can also react to it if required...
                    self.receive.put(packet)
                    break
                # Put other packets back to the Queue.
                self.receive.put(packet)
            except queue.Empty:
                continue
        # Return the current version info (might be None).
        return self._version_info
