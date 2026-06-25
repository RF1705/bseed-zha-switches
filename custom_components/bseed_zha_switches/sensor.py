"""Action sensor entities for BSEED TS0726 ZHA switches."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .const import DOMAIN, ZHA_DOMAIN
from .devices import BseedDevice, find_bseed_devices

EVENT_ZHA_EVENT = "zha_event"

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up BSEED action sensors."""

    entities = [BseedActionSensor(device) for device in find_bseed_devices(hass)]
    _LOGGER.info("Adding %s BSEED ZHA switch action sensors", len(entities))
    async_add_entities(entities)


class BseedActionSensor(SensorEntity, RestoreEntity):
    """Sensor showing the last BSEED scene action."""

    _attr_has_entity_name = True
    _attr_name = "Last action"

    def __init__(self, device: BseedDevice) -> None:
        """Initialize the action sensor."""

        self._device = device
        self._attr_unique_id = f"{DOMAIN}_{device.ieee}_last_action"
        self._attr_native_value: str | None = None
        self._attr_extra_state_attributes: dict[str, Any] = {}
        self._attr_device_info = {
            "identifiers": {(ZHA_DOMAIN, device.ieee)},
            "manufacturer": "BSEED",
            "model": device.model,
        }

    async def async_added_to_hass(self) -> None:
        """Restore state and start listening for ZHA events."""

        if (state := await self.async_get_last_state()) is not None:
            self._attr_native_value = None if state.state == "unknown" else state.state
            self._attr_extra_state_attributes = dict(state.attributes)

        self.async_on_remove(
            self.hass.bus.async_listen(EVENT_ZHA_EVENT, self._handle_zha_event)
        )

    @callback
    def _handle_zha_event(self, event: Event) -> None:
        """Update the sensor from a ZHA scene action event."""

        data = event.data
        ieee = str(data.get("device_ieee") or data.get("ieee") or "").lower()
        if ieee != self._device.ieee.lower():
            return

        command = data.get("command")
        if not isinstance(command, str) or not command.startswith("scene_"):
            return

        endpoint_id = data.get("endpoint_id")
        if endpoint_id is None:
            endpoint_id = _endpoint_from_scene_command(command)

        self._attr_native_value = command
        self._attr_extra_state_attributes = {
            "endpoint_id": endpoint_id,
            "device_ieee": self._device.ieee,
        }
        self.async_write_ha_state()


def _endpoint_from_scene_command(command: str) -> int | None:
    """Extract the endpoint number from scene_1, scene_2, ... commands."""

    try:
        return int(command.rsplit("_", 1)[1])
    except (IndexError, ValueError):
        return None
