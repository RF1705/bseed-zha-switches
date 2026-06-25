"""BSEED ZHA Switches integration."""

from __future__ import annotations

import logging

from .const import DOMAIN
from .runtime_quirks import install_runtime_attribute_defs

PLATFORMS = ["select"]

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass, config):
    """Set up BSEED ZHA Switches."""

    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass, entry):
    """Set up BSEED ZHA Switches from a config entry."""

    install_runtime_attribute_defs()

    try:
        from . import quirks  # noqa: F401
    except Exception:  # noqa: BLE001
        _LOGGER.exception("Failed to import bundled BSEED ZHA quirks")

    hass.data.setdefault(DOMAIN, {})
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass, entry):
    """Unload BSEED ZHA Switches."""

    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
