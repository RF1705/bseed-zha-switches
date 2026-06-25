"""Runtime Zigpy patches for already-paired BSEED TS0726 devices."""

from __future__ import annotations

import logging

import zigpy.types as t
from zigpy.zcl import Cluster
from zigpy.zcl.clusters.general import OnOff
from zigpy.zcl.foundation import ZCLAttributeDef

from .const import (
    ATTR_BACKLIGHT_MODE,
    ATTR_INDICATOR_MODE,
    ATTR_POWER_ON_BEHAVIOR,
    ATTR_SWITCH_MODE,
    TUYA_MANUFACTURER_CODE,
)

_LOGGER = logging.getLogger(__name__)


def install_runtime_attribute_defs() -> None:
    """Install TS0726 attributes on generic clusters used by existing devices."""

    _register_attribute(
        OnOff,
        "tuya_backlight_switch",
        ATTR_BACKLIGHT_MODE,
        t.enum8,
    )
    _register_attribute(
        OnOff,
        "tuya_indicator_mode",
        ATTR_INDICATOR_MODE,
        t.enum8,
    )
    _register_attribute(
        Cluster,
        "power_on_behavior",
        ATTR_POWER_ON_BEHAVIOR,
        t.enum8,
    )
    _register_attribute(
        Cluster,
        "switch_mode",
        ATTR_SWITCH_MODE,
        t.enum8,
    )


def _register_attribute(
    cluster_cls: type[Cluster],
    name: str,
    attr_id: int,
    attr_type: type,
) -> None:
    """Register a manufacturer-specific attribute on a Zigpy cluster class."""

    attr_def = ZCLAttributeDef(
        id=attr_id,
        type=attr_type,
        access="rw",
        manufacturer_code=TUYA_MANUFACTURER_CODE,
    )
    object.__setattr__(attr_def, "name", name)

    cluster_cls._attributes_by_id.setdefault(
        attr_def.id, {True: {}, False: {}, None: {}}
    )
    cluster_cls._attributes_by_id[attr_def.id][True][TUYA_MANUFACTURER_CODE] = attr_def
    cluster_cls.attributes[attr_def.id] = attr_def
    cluster_cls.attributes_by_name[name] = attr_def

    _LOGGER.debug(
        "Registered BSEED runtime attribute %s on %s: id=0x%04x manufacturer=0x%04x",
        name,
        cluster_cls.__name__,
        attr_id,
        TUYA_MANUFACTURER_CODE,
    )
