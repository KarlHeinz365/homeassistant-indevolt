from homeassistant.components.sensor import (
    SensorEntity, 
    SensorDeviceClass, 
    SensorEntityDescription, 
    SensorStateClass
)
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.util import dt as dt_util
from .const import DOMAIN
# ... other imports ...

class IndevoltSensorEntity(CoordinatorEntity, SensorEntity, RestoreEntity):
    def __init__(self, coordinator, description):
        super().__init__(coordinator)
        self.entity_description = description
        self._last_valid_value = None
        self._last_update_date = None

    async def async_added_to_hass(self):
        await super().async_added_to_hass()
        last_state = await self.async_get_last_state()
        if last_state and last_state.state not in (None, "unknown", "unavailable"):
            self._last_valid_value = float(last_state.state)
            self._last_update_date = dt_util.now().date()

    @property
    def native_value(self):
        raw_value = self.coordinator.data.get(self.entity_description.key)
        if raw_value is None:
            return self._last_valid_value
            
        new_value = raw_value * self.entity_description.coefficient
        current_date = dt_util.now().date()

        # Daily Reset Safeguard logic
        if self.entity_description.state_class == SensorStateClass.TOTAL_INCREASING:
            # 1. Allow midnight reset
            if self._last_update_date and current_date > self._last_update_date:
                self._last_valid_value = new_value
                self._last_update_date = current_date
                return new_value
            
            # 2. Glitch protection: Ignore sudden drops to zero during the same day
            if self._last_valid_value is not None and new_value < (self._last_valid_value - 0.1):
                # If it's still the same day, this is likely a communication glitch
                return self._last_valid_value
            
            self._last_valid_value = new_value
            self._last_update_date = current_date
            
        return new_value
