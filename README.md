# BSEED ZHA Switches

Home Assistant HACS integration for BSEED TS0726 ZHA switches.

Supported devices:

- BSEED EC-GL86ZPCS11, 1-gang, `_TZ3002_jn2x20tg`
- BSEED EC-GL86ZPCS21, 2-gang, `_TZ3002_zjuvw9zf`

The integration creates dropdown entities for:

- Backlight mode: `off`, `on`
- Indicator mode: `none`, `relay`, `pos`
- Switch mode per channel: `switch`, `scene`
- Power-on behavior per channel: `off`, `on`, `previous`

It also bundles ZHA quirk classes for the two switches. The bundled quirks add:

- BSEED manufacturer/model display names
- TS0726 Tuya option cluster definitions
- `scene_1` / `scene_2` ZHA events in scene mode

## Installation with HACS

1. In HACS, open **Custom repositories**.
2. Add this repository URL.
3. Category: **Integration**.
4. Install **BSEED ZHA Switches**.
5. Restart Home Assistant.
6. Go to **Settings > Devices & services > Add integration**.
7. Add **BSEED ZHA Switches**.

The integration scans the Home Assistant device registry for supported ZHA
devices and attaches the select entities to the existing ZHA device.

## Important ZHA quirk note

Home Assistant loads ZHA quirks when a Zigbee device is initialized. This
integration imports its bundled quirk classes when the integration is loaded,
but already-initialized ZHA devices may keep their old quirk assignment.

For the most reliable result:

1. Install this integration.
2. Restart Home Assistant.
3. Re-pair the BSEED switch if the device still shows the raw Tuya model or if
   scene events are missing.

The select entities do not require the quirk to be active. They work as long as
the device is present in Home Assistant as one of these:

- `_TZ3002_jn2x20tg / TS0726`
- `_TZ3002_zjuvw9zf / TS0726`
- `BSEED / EC-GL86ZPCS11`
- `BSEED / EC-GL86ZPCS21`

## Notes

The select entities are optimistic. Home Assistant stores the last selected
option, but the integration does not currently read the option values back from
the switch after a restart.
