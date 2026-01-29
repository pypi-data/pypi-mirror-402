from datetime import datetime
from enum import IntEnum
from typing import Any, Callable, Coroutine, TypedDict
from enocean.protocol.packet import RadioPacket


type EnOceanEntityUID = str | None
"""A string identifiying the entity uniquely within the context of an EnOcean device's platform.

Uniqueness is only per device and platform, thus, the same UID can be used for a binary sensor and a light entity of the same device.
"""

type EnOceanDeviceIDString = str
"""An EnOcean device ID as string"""

type EnOceanSendRadioPacket = Callable[[RadioPacket], None]

# Callbacks for state updates
type EnOceanBinarySensorCallback = Callable[[bool], None]
"""Callback type for binary sensor state changes, with a boolean parameter indicating the new is_on state."""

type EnOceanCoverCallback = Callable[[int], None]
"""Callback type for cover state changes, with new position (closed = 0, fully open = 100)."""

type EnOceanEventCallback = Callable[[str, dict], None]
"""Callback type for event notifications, with event type as string and additional data as dictionary."""

type EnOceanLightCallback = Callable[[bool, int, int], None]
"""Callback type for light state changes, with is_on state, brightness (1..255) and color temperature (in Kelvin) as parameters."""

type EnOceanSensorCallback = Callable[[float | datetime], None]
"""Callback type for binary sensor state changes, with a numeric parameter indicating the new state."""

type EnOceanSwitchCallback = Callable[[bool], None]
"""Callback type for switch state changes, with a boolean parameter indicating the new is_on state."""


class ValueLabelDict(TypedDict):
    """Representation of a value/label dictionary."""

    def __init__(self, value: str, label: str) -> None:
        """Construct a value/label dictionary."""
        self.value = value
        self.label = label


class COMMON_COMMAND(IntEnum):
    CO_RD_VERSION = 0x03
    CO_RD_IDBASE = 0x08


class VersionIdentifier:
    main: int = 0
    beta: int = 0
    alpha: int = 0
    build: int = 0

    def versionString(self) -> str:
        return f"{self.main}.{self.beta}.{self.alpha}{f'b{self.build}' if self.build else ''}"


class VersionInfo:
    app_version: VersionIdentifier = VersionIdentifier()
    api_version: VersionIdentifier = VersionIdentifier()
    chip_id: 0
    chip_version = 0
    app_description = ""


type HomeAssistantTaskCreator = Callable[[Coroutine[Any, Any, Any], str | None], None]
