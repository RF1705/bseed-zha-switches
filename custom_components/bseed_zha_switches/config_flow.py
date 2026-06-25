"""Config flow for BSEED ZHA Switches."""

from __future__ import annotations

from homeassistant import config_entries


class BseedZhaSwitchesConfigFlow(
    config_entries.ConfigFlow, domain="bseed_zha_switches"
):
    """Handle a config flow for BSEED ZHA Switches."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Create the single integration entry."""

        await self.async_set_unique_id("bseed_zha_switches")
        self._abort_if_unique_id_configured()

        return self.async_create_entry(title="BSEED ZHA Switches", data={})
