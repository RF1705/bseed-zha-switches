"""Device discovery helpers for BSEED ZHA Switches."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import (
    CONNECTION_NETWORK_MAC,
    DeviceEntry,
    async_get as async_get_dr,
)

from .const import (
    BSEED_MANUFACTURER,
    MANUFACTURER_1_GANG,
    MANUFACTURER_2_GANG,
    MODEL_1_GANG,
    MODEL_2_GANG,
    RAW_MODEL,
    ZHA_DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class BseedDevice:
    """Detected BSEED device data."""

    ieee: str
    model: str
    channels: int


def find_bseed_devices(hass: HomeAssistant) -> list[BseedDevice]:
    """Find supported ZHA BSEED TS0726 devices in the device registry."""

    registry = async_get_dr(hass)
    devices: list[BseedDevice] = []

    for device in registry.devices.values():
        ieee = _ieee_from_device(device)
        if ieee is None:
            continue

        bseed_device = _match_bseed_device(device, ieee)
        if bseed_device is None:
            continue

        _LOGGER.info(
            "Found BSEED ZHA switch: ieee=%s model=%s channels=%s",
            bseed_device.ieee,
            bseed_device.model,
            bseed_device.channels,
        )
        devices.append(bseed_device)

    return devices


def _match_bseed_device(device: DeviceEntry, ieee: str) -> BseedDevice | None:
    """Match a Home Assistant device registry entry to a supported BSEED switch."""

    manufacturer = device.manufacturer or ""
    model = device.model or ""
    text = " ".join(
        str(value)
        for value in (
            manufacturer,
            model,
            getattr(device, "name", None),
            getattr(device, "name_by_user", None),
        )
        if value
    )

    if manufacturer == MANUFACTURER_1_GANG:
        return BseedDevice(ieee=ieee, model=MODEL_1_GANG, channels=1)

    if manufacturer == MANUFACTURER_2_GANG:
        return BseedDevice(ieee=ieee, model=MODEL_2_GANG, channels=2)

    if model == MODEL_1_GANG or MODEL_1_GANG in text:
        return BseedDevice(ieee=ieee, model=MODEL_1_GANG, channels=1)

    if model == MODEL_2_GANG or MODEL_2_GANG in text:
        return BseedDevice(ieee=ieee, model=MODEL_2_GANG, channels=2)

    if manufacturer == BSEED_MANUFACTURER and model == RAW_MODEL:
        _LOGGER.warning(
            "Found BSEED TS0726 device without exact model information: ieee=%s. "
            "Assuming EC-GL86ZPCS21 with 2 channels.",
            ieee,
        )
        return BseedDevice(ieee=ieee, model=MODEL_2_GANG, channels=2)

    return None


def _ieee_from_device(device: DeviceEntry) -> str | None:
    """Extract the ZHA IEEE identifier from a Home Assistant device entry."""

    for identifier in device.identifiers:
        if len(identifier) < 2:
            continue

        domain = identifier[0]
        value = identifier[1]

        if domain == ZHA_DOMAIN:
            return str(value)

    for connection in device.connections:
        if len(connection) < 2:
            continue

        connection_type = connection[0]
        address = connection[-1]

        if connection_type == CONNECTION_NETWORK_MAC:
            return str(address)

    return None
