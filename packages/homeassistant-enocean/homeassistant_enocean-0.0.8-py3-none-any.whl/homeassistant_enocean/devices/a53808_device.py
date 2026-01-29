import math

from homeassistant_enocean.types import EnOceanEntityUID
from .device import EnOceanDevice
from ..entity_properties import HomeAssistantEntityProperties
from enocean.protocol.packet import RadioPacket

RORG_4BS = 0xA5
FUNC = 0x38
CMD_DIMMING = 0x02

EDIMR_ABSOLUTE = 0
EDIMR_RELATIVE = 1


class EnOceanA53808Device(EnOceanDevice):
    """Handler for EnOcean Equipment Profile A5-38-08 (Gateway)"""

    def initialize_entities(self) -> None:
        """Initialize the entities handled by this EEP handler."""
        self.__min_brightness = 0
        self.__max_brightness = 100
        self.__brightness_range = 100
        self.__ramping_time = 1

        self._light_entities = [
            HomeAssistantEntityProperties(unique_id=None, device_class="light"),
        ]

        self._number_entities = [
            HomeAssistantEntityProperties(
                unique_id="ramping_time",
                native_min_value=0,
                native_max_value=255,
                native_step=1,
                native_value=1,
                entity_category="diagnostic",
                native_unit_of_measurement="s",
                device_class="duration",
            ),
            HomeAssistantEntityProperties(
                unique_id="min_brightness",
                native_min_value=1,
                native_max_value=100,
                native_step=1,
                native_value=1,
                entity_category="diagnostic",
                native_unit_of_measurement="%",
            ),
            HomeAssistantEntityProperties(
                unique_id="max_brightness",
                native_min_value=0,
                native_max_value=100,
                native_step=1,
                native_value=100,
                entity_category="diagnostic",
                native_unit_of_measurement="%",
            ),
        ]

        self._sensor_entities = [
            HomeAssistantEntityProperties(
                unique_id="device_brightness",
                device_class="percentage",
                native_unit_of_measurement="%",
                entity_category="diagnostic",
            ),
            HomeAssistantEntityProperties(
                unique_id="dimming_range",
                device_class="enum",
                options=["0 - 255", "0 - 100"],
                entity_category="diagnostic",
            ),
        ]

    def handle_matching_packet(self, packet) -> None:
        """Handle an incoming EnOcean packet."""

        # ignore non A5 packets
        if packet.rorg != RORG_4BS:
            return

        # ignore commands other than 2
        if packet.data[1] != CMD_DIMMING:
            return

        edim = 0
        edimr = 0
        sw = 0

        try:
            packet.parse_eep(rorg_func=FUNC, rorg_type=0x08, command=CMD_DIMMING)
            edim = packet.parsed["EDIM"]["raw_value"]
            edimr = packet.parsed["EDIMR"]["raw_value"]
            sw = packet.parsed["SW"]["raw_value"]

        except Exception:
            return

        dimming_range = "0 - 255" if edimr == EDIMR_ABSOLUTE else "0 - 100"
        dimming_range_callback = self._sensor_callbacks.get("dimming_range")
        if dimming_range_callback:
            dimming_range_callback(dimming_range)

        device_brightness_relative = (
            edim if edimr == EDIMR_RELATIVE else edim * 100 / 255.0
        )
        device_brightness_callback = self._sensor_callbacks.get("device_brightness")
        if device_brightness_callback:
            device_brightness_callback(device_brightness_relative)

        homeassistant_brightness = self.convert_relative_device_brightness_to_absolute_home_assistant_brightness(
            device_brightness_relative / 100.0
        )
        light_callback = self._light_callbacks.get(None)
        if light_callback:
            light_callback(sw > 0, homeassistant_brightness, 0)

    def light_turn_off(self, entity_uid: EnOceanEntityUID) -> None:
        """Turn the light source off."""
        packet = RadioPacket.create(
            rorg=RORG_4BS,
            rorg_func=FUNC,
            rorg_type=0x08,
            command=CMD_DIMMING,  # command 2 (set dimmer)
            destination=self.enocean_id.to_bytelist(),
            sender=self.sender_id.to_bytelist(),
            COM=CMD_DIMMING,  # command 2 (set dimmer)
            EDIM=0,
            RMP=self.__ramping_time,
            EDIMR=0,
            STR=0,
            SW=0,
        )
        self.send_packet(packet)

        light_callback = self._light_callbacks.get(None)
        if light_callback:
            light_callback(False, 0, 0)

    @property
    def _min_brightness(self) -> int:
        """Get the minimum device brightness value in interval [0, self._max_brightness] with 0<self._max_brightness<=100."""
        return self.__min_brightness

    @property
    def _max_brightness(self) -> int:
        """Get the maximum device brightness value in interval [self._min_brightness, 100] with 0<=self._min_brightness<=100."""
        return self.__max_brightness

    @property
    def _brightness_range(self) -> int:
        """Get the brightness range, i.e. self._max_brightness - self._min_brightness."""
        return self.__brightness_range

    @_min_brightness.setter
    def _min_brightness(self, value: int) -> None:
        """Set the minimum brightness value in interval [0, self._max_brightness].
        If the given value is less than 0, it is set to 0.
        If the given value is greater than self._max_brightness, it is set to self._max_brightness.
        """
        if value < 0:
            self.__min_brightness = 0
        elif value > self._max_brightness:
            self.__min_brightness = self._max_brightness
        else:
            self.__min_brightness = value

        self.__brightness_range = self.__max_brightness - self.__min_brightness

    @_max_brightness.setter
    def _max_brightness(self, value: int) -> None:
        """Set the maximum brightness value in interval [self._min_brightness, 100].
        If the given value is greater than 100, it is set to 100.
        If the given value is less than self._min_brightness, it is set to self._min_brightness.
        """
        if value > 100:
            self.__max_brightness = 100
        elif value < self._min_brightness:
            self.__max_brightness = self._min_brightness
        else:
            self.__max_brightness = value

        self.__brightness_range = self.__max_brightness - self.__min_brightness

    def light_turn_on(
        self,
        entity_uid: EnOceanEntityUID,
        brightness: int | None = None,
        color_temp_kelvin: int | None = None,
    ) -> None:
        """Turn the light source on or sets a specific dimmer value."""
        if brightness is None:
            brightness = 255

        # 1. set device brightness by sending the respective EnOcean telegram
        packet = RadioPacket.create(
            rorg=RORG_4BS,
            rorg_func=FUNC,
            rorg_type=0x08,
            command=CMD_DIMMING,  # command 2 (set dimmer)
            destination=self.enocean_id.to_bytelist(),
            sender=self.sender_id.to_bytelist(),
            COM=CMD_DIMMING,  # command 2 (set dimmer)
            EDIM=100
            * self.convert_absolute_home_assistant_brightness_to_relative_device_brightness(
                brightness
            ),
            RMP=self.__ramping_time,
            EDIMR=1,
            STR=0,
            SW=1,
        )
        self.send_packet(packet)

        # 2. call the callback to update the state in Home Assistant (optimistic update)
        light_callback = self._light_callbacks.get(None)
        if light_callback:
            light_callback(brightness > 0, brightness, 0)

    def set_number_value(self, entity_uid: EnOceanEntityUID, value: float) -> None:
        """Set the value of a number entity."""

        match entity_uid:
            case "min_brightness":
                self._min_brightness = int(value)
            case "max_brightness":
                self._max_brightness = int(value)

            case "ramping_time":
                int_value = int(value)
                if int_value < 0:
                    int_value = 0
                elif int_value > 255:
                    int_value = 255
                self.__ramping_time = int_value

    def convert_relative_device_brightness_to_absolute_home_assistant_brightness(
        self, relative_device_brightness: float
    ) -> float:
        """Convert a relative brightness value in [0, 1] to an absolute brightness value in Home Assistant range [0..255].

        Note that the device brightness is expected to be in the range [min_brightness..max_brightness], but a value in [0..255] needs to be converted as well, as the device might be in a state not set by Home Assistant.
        """

        if relative_device_brightness * 100.0 < self._min_brightness:
            return 0.0
        elif relative_device_brightness * 100.0 > self._max_brightness:
            return 100.0

        ha_brightness = (
            (100.0 * relative_device_brightness - self._min_brightness)
            / self._brightness_range
        ) * 255.0

        return math.floor(ha_brightness)

    def convert_absolute_home_assistant_brightness_to_relative_device_brightness(
        self, absolute_homeassistant_brightness: float
    ) -> float:
        """Convert an absolute brightness value in Home Assistant interval [0, 255] to a relative brightness value in [min_brightness..max_brightness]."""
        device_brightness = (
            self._min_brightness / 100.0
            + (self._brightness_range / 25000.0) * absolute_homeassistant_brightness
        )
        return device_brightness
