"""BSEED ZHA Switches integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN

PLATFORMS = [Platform.SELECT]

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up BSEED ZHA Switches from a config entry."""

    try:
        from . import quirks  # noqa: F401
    except Exception:  # noqa: BLE001
        _LOGGER.exception("Failed to import bundled BSEED ZHA quirks")

    hass.data.setdefault(DOMAIN, {})
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload BSEED ZHA Switches."""

    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
