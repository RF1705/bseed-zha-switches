"""Select entities for BSEED TS0726 ZHA switches."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .const import (
    ATTR_BACKLIGHT_MODE,
    ATTR_INDICATOR_MODE,
    ATTR_POWER_ON_BEHAVIOR,
    ATTR_SWITCH_MODE,
    CLUSTER_ON_OFF,
    CLUSTER_TUYA_OPTIONS,
    DOMAIN,
    OPTION_BACKLIGHT,
    OPTION_INDICATOR,
    OPTION_POWER_ON,
    OPTION_SWITCH_MODE,
    ZHA_DOMAIN,
)
from .devices import BseedDevice, find_bseed_devices


_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class SelectDescription:
    """Description for a BSEED select entity."""

    key: str
    name: str
    endpoint_id: int
    cluster_id: int
    attribute_id: int
    options: dict[str, int]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up BSEED select entities."""

    entities: list[BseedZhaSelectEntity] = []

    for device in find_bseed_devices(hass):
        for description in _descriptions_for_device(device):
            entities.append(BseedZhaSelectEntity(device, description))

    _LOGGER.info("Adding %s BSEED ZHA switch select entities", len(entities))
    async_add_entities(entities)


def _descriptions_for_device(device: BseedDevice) -> list[SelectDescription]:
    """Return all select descriptions for a supported BSEED device."""

    descriptions = [
        SelectDescription(
            key="backlight_mode",
            name="Backlight mode",
            endpoint_id=1,
            cluster_id=CLUSTER_ON_OFF,
            attribute_id=ATTR_BACKLIGHT_MODE,
            options=OPTION_BACKLIGHT,
        ),
        SelectDescription(
            key="indicator_mode",
            name="Indicator mode",
            endpoint_id=1,
            cluster_id=CLUSTER_ON_OFF,
            attribute_id=ATTR_INDICATOR_MODE,
            options=OPTION_INDICATOR,
        ),
    ]

    for endpoint_id in range(1, device.channels + 1):
        suffix = f"l{endpoint_id}"
        descriptions.extend(
            [
                SelectDescription(
                    key=f"switch_mode_{suffix}",
                    name=f"Switch mode {suffix.upper()}",
                    endpoint_id=endpoint_id,
                    cluster_id=CLUSTER_TUYA_OPTIONS,
                    attribute_id=ATTR_SWITCH_MODE,
                    options=OPTION_SWITCH_MODE,
                ),
                SelectDescription(
                    key=f"power_on_behavior_{suffix}",
                    name=f"Power-on behavior {suffix.upper()}",
                    endpoint_id=endpoint_id,
                    cluster_id=CLUSTER_TUYA_OPTIONS,
                    attribute_id=ATTR_POWER_ON_BEHAVIOR,
                    options=OPTION_POWER_ON,
                ),
            ]
        )

    return descriptions


class BseedZhaSelectEntity(SelectEntity, RestoreEntity):
    """BSEED ZHA select entity backed by a ZHA cluster attribute."""

    _attr_has_entity_name = True

    def __init__(self, device: BseedDevice, description: SelectDescription) -> None:
        """Initialize the select entity."""

        self._device = device
        self._description = description
        self._current_option: str | None = None

        self._attr_unique_id = f"{DOMAIN}_{device.ieee}_{description.key}"
        self._attr_translation_key = description.key
        self._attr_name = description.name
        self._attr_options = list(description.options)
        self._attr_device_info = {
            "identifiers": {(ZHA_DOMAIN, device.ieee)},
            "manufacturer": "BSEED",
            "model": device.model,
        }

    @property
    def current_option(self) -> str | None:
        """Return the current selected option."""

        return self._current_option

    async def async_added_to_hass(self) -> None:
        """Restore the last selected option."""

        if (state := await self.async_get_last_state()) is not None:
            if state.state in self._description.options:
                self._current_option = state.state

    async def async_select_option(self, option: str) -> None:
        """Set the option on the Zigbee device."""

        value = self._description.options[option]
        _LOGGER.info(
            "Setting BSEED option: ieee=%s endpoint=%s cluster=0x%04x "
            "attribute=0x%04x option=%s value=%s",
            self._device.ieee,
            self._description.endpoint_id,
            self._description.cluster_id,
            self._description.attribute_id,
            option,
            value,
        )

        await self.hass.services.async_call(
            ZHA_DOMAIN,
            "set_zigbee_cluster_attribute",
            {
                "ieee": self._device.ieee,
                "endpoint_id": self._description.endpoint_id,
                "cluster_id": self._description.cluster_id,
                "cluster_type": "in",
                "attribute": self._description.attribute_id,
                "value": value,
            },
            blocking=True,
        )

        self._current_option = option
        self.async_write_ha_state()
