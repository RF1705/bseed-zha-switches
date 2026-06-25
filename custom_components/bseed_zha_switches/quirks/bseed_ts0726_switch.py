"""ZHA custom quirks for BSEED/Tuya TS0726 1- and 2-gang scene switches.

Confirmed BSEED variants:
    EC-GL86ZPCS11: _TZ3002_jn2x20tg / TS0726
    EC-GL86ZPCS21: _TZ3002_zjuvw9zf / TS0726

Zigbee2MQTT equivalent functionality:
    state_l1/state_l2
    countdown/countdown_l1/countdown_l2 via OnOff on_with_timed_off/on_time
    power_on_behavior_l1/power_on_behavior_l2: off, on, previous
    switch_mode_l1/switch_mode_l2: switch, scene
    backlight_mode: off, on
    indicator_mode: none, relay, pos
    action: scene_1, scene_2

Copy this file to:
    /config/custom_zha_quirks/bseed_ts0726_switch.py

Then add this to configuration.yaml:
    zha:
      custom_quirks_path: /config/custom_zha_quirks

Restart Home Assistant and reconfigure or re-pair the switch if needed.
"""

from typing import Final

import zigpy.types as t
from zigpy.profiles import zha
from zigpy.quirks import CustomDevice
from zigpy.zcl import BaseAttributeDefs, foundation
from zigpy.zcl.clusters.general import (
    Basic,
    Groups,
    Identify,
    OnOff,
    Ota,
    Scenes,
    Time,
)
from zigpy.zcl.foundation import ZCLAttributeDef, ZCLCommandDef

from zhaquirks import EventableCluster
from zhaquirks.clusters import CustomCluster
from zhaquirks.const import (
    DEVICE_TYPE,
    ENDPOINTS,
    INPUT_CLUSTERS,
    MODELS_INFO,
    OUTPUT_CLUSTERS,
    PROFILE_ID,
    ZHA_SEND_EVENT,
)
from zhaquirks.tuya import TuyaZBE000Cluster


PROFILE_GREEN_POWER = 0xA1E0
DEVICE_TYPE_GREEN_POWER_PROXY = 0x0061
GREEN_POWER_CLUSTER = 0x0021

DEVICE_TYPE_TS0726_SWITCH = 0x0004
MANUFACTURER_1_GANG = "_TZ3002_jn2x20tg"
MANUFACTURER_2_GANG = "_TZ3002_zjuvw9zf"
MODEL = "TS0726"
MODEL_1_GANG = "EC-GL86ZPCS11"
MODEL_2_GANG = "EC-GL86ZPCS21"


class BseedTS0726BasicCluster(CustomCluster, Basic):
    """Base Basic cluster showing the real BSEED manufacturer name."""

    _CONSTANT_ATTRIBUTES = {
        0x0004: "BSEED",
    }


class BseedTS0726BasicCluster1Gang(BseedTS0726BasicCluster):
    """Basic cluster for BSEED EC-GL86ZPCS11."""

    _CONSTANT_ATTRIBUTES = {
        **BseedTS0726BasicCluster._CONSTANT_ATTRIBUTES,
        0x0005: MODEL_1_GANG,
    }


class BseedTS0726BasicCluster2Gang(BseedTS0726BasicCluster):
    """Basic cluster for BSEED EC-GL86ZPCS21."""

    _CONSTANT_ATTRIBUTES = {
        **BseedTS0726BasicCluster._CONSTANT_ATTRIBUTES,
        0x0005: MODEL_2_GANG,
    }


class BseedBacklightMode(t.enum8):
    """Backlight mode on the standard OnOff cluster."""

    Off = 0x00
    On = 0x01


class BseedIndicatorMode(t.enum8):
    """LED indicator mode on the standard OnOff cluster."""

    None_ = 0x00
    Relay = 0x01
    Position = 0x02


class BseedPowerOnBehavior(t.enum8):
    """Power-on behavior used by TS0726 on cluster 0xE001."""

    Off = 0x00
    On = 0x01
    Previous = 0x02


class BseedSwitchMode(t.enum8):
    """Physical button behavior used by TS0726 on cluster 0xE001."""

    Switch = 0x00
    Scene = 0x01


class BseedSwitchType(t.enum8):
    """External switch type on cluster 0xE001."""

    Toggle = 0x00
    State = 0x01
    Momentary = 0x02


class BseedTS0726OnOffCluster(CustomCluster, OnOff, EventableCluster):
    """OnOff cluster with TS0726 backlight attributes and scene actions."""

    class AttributeDefs(OnOff.AttributeDefs):
        """Tuya attributes added to the OnOff cluster."""

        tuya_backlight_switch: Final = ZCLAttributeDef(
            id=0x5000, type=BseedBacklightMode
        )
        tuya_indicator_mode: Final = ZCLAttributeDef(
            id=0x8001, type=BseedIndicatorMode
        )
        moes_start_up_on_off: Final = ZCLAttributeDef(
            id=0x8002, type=BseedPowerOnBehavior
        )
        tuya_operation_mode: Final = ZCLAttributeDef(
            id=0x8004, type=BseedSwitchMode
        )

    class ServerCommandDefs(OnOff.ServerCommandDefs):
        """Tuya scene action commands sent by the switch in scene mode."""

        tuya_action_2: Final = ZCLCommandDef(
            id=0xFC,
            schema={"value": t.uint8_t},
            is_manufacturer_specific=True,
        )
        tuya_action: Final = ZCLCommandDef(
            id=0xFD,
            schema={"value": t.uint8_t},
            is_manufacturer_specific=True,
        )

    def __init__(self, *args, **kwargs):
        """Initialize duplicate-frame tracking for scene events."""

        self._last_action_tsn = None
        super().__init__(*args, **kwargs)

    def handle_cluster_request(
        self,
        hdr: foundation.ZCLHeader,
        args: list,
        *,
        dst_addressing=None,
    ) -> None:
        """Emit ZHA events for TS0726 scene-mode button presses."""

        if hdr.command_id not in (0xFC, 0xFD):
            return super().handle_cluster_request(
                hdr, args, dst_addressing=dst_addressing
            )

        if not hdr.frame_control.disable_default_response:
            self.send_default_rsp(hdr, status=foundation.Status.SUCCESS)

        if self._last_action_tsn == hdr.tsn:
            return

        self._last_action_tsn = hdr.tsn
        self.listener_event(
            ZHA_SEND_EVENT,
            f"scene_{self.endpoint.endpoint_id}",
            [],
        )


class BseedTS0726E001Cluster(CustomCluster):
    """TS0726 manufacturer cluster 0xE001.

    Zigbee2MQTT names this cluster manuSpecificTuya3 and uses it for
    power_on_behavior, switch_mode and switch_type.
    """

    name = "BSEED TS0726 Tuya options"
    cluster_id = 0xE001
    ep_attribute = "bseed_ts0726_options"

    class AttributeDefs(BaseAttributeDefs):
        """Tuya option attributes."""

        power_on_behavior: Final = ZCLAttributeDef(
            id=0xD010, type=BseedPowerOnBehavior
        )
        switch_mode: Final = ZCLAttributeDef(
            id=0xD020, type=BseedSwitchMode
        )
        switch_type: Final = ZCLAttributeDef(
            id=0xD030, type=BseedSwitchType
        )


def green_power_endpoint():
    """Return the Green Power proxy endpoint used by these switches."""

    return {
        PROFILE_ID: PROFILE_GREEN_POWER,
        DEVICE_TYPE: DEVICE_TYPE_GREEN_POWER_PROXY,
        INPUT_CLUSTERS: [],
        OUTPUT_CLUSTERS: [GREEN_POWER_CLUSTER],
    }


def endpoint_1_signature():
    """Return endpoint 1 as reported by both BSEED TS0726 variants."""

    return {
        PROFILE_ID: zha.PROFILE_ID,
        DEVICE_TYPE: DEVICE_TYPE_TS0726_SWITCH,
        INPUT_CLUSTERS: [
            Basic.cluster_id,
            Identify.cluster_id,
            Groups.cluster_id,
            Scenes.cluster_id,
            OnOff.cluster_id,
            TuyaZBE000Cluster.cluster_id,
            BseedTS0726E001Cluster.cluster_id,
        ],
        OUTPUT_CLUSTERS: [
            Time.cluster_id,
            Ota.cluster_id,
        ],
    }


def endpoint_2_signature():
    """Return endpoint 2 as reported by the 2-gang switch."""

    return {
        PROFILE_ID: zha.PROFILE_ID,
        DEVICE_TYPE: DEVICE_TYPE_TS0726_SWITCH,
        INPUT_CLUSTERS: [
            Groups.cluster_id,
            Scenes.cluster_id,
            OnOff.cluster_id,
            BseedTS0726E001Cluster.cluster_id,
        ],
        OUTPUT_CLUSTERS: [],
    }


def endpoint_1_replacement(basic_cluster):
    """Return endpoint 1 with TS0726 custom clusters installed."""

    return {
        PROFILE_ID: zha.PROFILE_ID,
        DEVICE_TYPE: DEVICE_TYPE_TS0726_SWITCH,
        INPUT_CLUSTERS: [
            basic_cluster,
            Identify.cluster_id,
            Groups.cluster_id,
            Scenes.cluster_id,
            BseedTS0726OnOffCluster,
            TuyaZBE000Cluster,
            BseedTS0726E001Cluster,
        ],
        OUTPUT_CLUSTERS: [
            Time.cluster_id,
            Ota.cluster_id,
        ],
    }


def endpoint_2_replacement():
    """Return endpoint 2 with TS0726 custom clusters installed."""

    return {
        PROFILE_ID: zha.PROFILE_ID,
        DEVICE_TYPE: DEVICE_TYPE_TS0726_SWITCH,
        INPUT_CLUSTERS: [
            Groups.cluster_id,
            Scenes.cluster_id,
            BseedTS0726OnOffCluster,
            BseedTS0726E001Cluster,
        ],
        OUTPUT_CLUSTERS: [],
    }


class BseedTS0726Switch1Gang(CustomDevice):
    """BSEED EC-GL86ZPCS11 1-gang scene switch."""

    signature = {
        MODELS_INFO: [(MANUFACTURER_1_GANG, MODEL)],
        ENDPOINTS: {
            1: endpoint_1_signature(),
            242: green_power_endpoint(),
        },
    }

    replacement = {
        ENDPOINTS: {
            1: endpoint_1_replacement(BseedTS0726BasicCluster1Gang),
            242: green_power_endpoint(),
        },
    }


class BseedTS0726Switch2Gang(CustomDevice):
    """BSEED EC-GL86ZPCS21 2-gang scene switch."""

    signature = {
        MODELS_INFO: [(MANUFACTURER_2_GANG, MODEL)],
        ENDPOINTS: {
            1: endpoint_1_signature(),
            2: endpoint_2_signature(),
            242: green_power_endpoint(),
        },
    }

    replacement = {
        ENDPOINTS: {
            1: endpoint_1_replacement(BseedTS0726BasicCluster2Gang),
            2: endpoint_2_replacement(),
            242: green_power_endpoint(),
        },
    }
