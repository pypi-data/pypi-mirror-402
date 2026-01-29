import datetime


class HomeAssistantEntityProperties:
    """A collection of properties for a Home Assistant entity."""

    def __init__(
        self,
        unique_id: str | None = None,
        device_class: str | None = None,
        supported_features: int | None = None,
        translation_key: str | None = None,
        event_types: list[str] | None = None,
        native_unit_of_measurement: str | None = None,
        last_reset: datetime.datetime | None = None,
        sensor_state_class: str | None = None,
        entity_category: str | None = None,
        options: list | None = None,
        current_option: str | None = None,
        native_max_value: float | None = None,
        native_min_value: float | None = None,
        native_step: float | None = None,
        native_value: float | None = None,
    ) -> None:
        self.unique_id: str | None = unique_id
        self.device_class: str | None = device_class
        self.supported_features: int | None = (
            supported_features  # Bitmask of supported features
        )
        self.translation_key: str | None = translation_key
        self.event_types: list[str] = event_types
        self.platform: str | None = (
            None  # e.g., 'binary_sensor', 'cover', 'light', 'switch'
        )
        self.state_class: str | None = sensor_state_class
        self.native_unit_of_measurement: str | None = native_unit_of_measurement
        self.last_reset: datetime.datetime | None = last_reset
        self.entity_category: str | None = (
            entity_category  # e.g., 'diagnostic', 'config'
        )
        self.options: list | None = options  # For select entities
        self.current_option: str | None = current_option  # For select entities
        self.native_max_value: float | None = native_max_value  # For number entities
        self.native_min_value: float | None = native_min_value  # For number entities
        self.native_step: float | None = native_step  # For number entities
        self.native_value: float | None = native_value  # For number entities

    def __str__(self):
        return (
            f"HomeAssistantEntityProperties("
            f"unique_id={self.unique_id}, "
            f"device_class={self.device_class}, "
            f"supported_features={self.supported_features}, "
            f"translation_key={self.translation_key}, "
            f"event_types={self.event_types})"
        )
