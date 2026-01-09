import asyncio, aiohttp, json
from typing import Dict, Any, List
import logging

_LOGGER = logging.getLogger(__name__)

class IndevoltAPI:
    def __init__(self, host: str, port: int, session: aiohttp.ClientSession):
        self.host, self.port, self.session = host, port, session
        self.base_url = f"http://{host}:{port}/rpc"

    async def fetch_data(self, keys: List[int]) -> Dict[str, Any]:
        """Fetch data from specific registers."""
        config = json.dumps({"t": keys}).replace(" ", "")
        try:
            async with self.session.post(
                f"{self.base_url}/Indevolt.GetData?config={config}", 
                timeout=aiohttp.ClientTimeout(total=15)
            ) as resp:
                if resp.status == 200:
                    return await resp.json()
                else:
                    _LOGGER.error(f"Failed to fetch data: HTTP {resp.status}")
                    return {}
        except asyncio.TimeoutError:
            _LOGGER.error("Timeout while fetching data")
            return {}
        except Exception as e:
            _LOGGER.error(f"Error fetching data: {e}")
            return {}

    async def set_data(self, f: int, t: int, v: list) -> dict:
        """Write data to registers."""
        config = json.dumps({"f": f, "t": t, "v": v}).replace(" ", "")
        try:
            async with self.session.post(
                f"{self.base_url}/Indevolt.SetData?config={config}", 
                timeout=aiohttp.ClientTimeout(total=15)
            ) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    _LOGGER.debug(f"Set data response: {result}")
                    return result
                else:
                    _LOGGER.error(f"Failed to set data: HTTP {resp.status}")
                    return {"result": False, "error": f"HTTP {resp.status}"}
        except asyncio.TimeoutError:
            _LOGGER.error("Timeout while setting data")
            return {"result": False, "error": "Timeout"}
        except Exception as e:
            _LOGGER.error(f"Error setting data: {e}")
            return {"result": False, "error": str(e)}

    # ==================== Mode Control ====================
    async def async_set_mode(self, mode: int) -> dict:
        """
        Set the device working mode (Register 47005).
        1: Self-consumed prioritized
        2: Charge/Discharge Schedule
        4: Real-time control
        5: Charge/Discharge Schedule (alternative)
        """
        _LOGGER.info(f"Setting working mode to {mode}")
        return await self.set_data(16, 47005, [mode])

    # ==================== Battery Control (Real-time Mode) ====================
    async def async_charge(self, power: int, soc_limit: int = 100, max_power: int = 1200) -> dict:
        """
        Charge battery in real-time control mode.
        Register 47015: [state=1, power, soc_limit]
        """
        clamped_power = min(power, max_power)
        _LOGGER.info(f"Charging battery: {clamped_power}W, SOC limit: {soc_limit}%")
        return await self.set_data(16, 47015, [1, clamped_power, soc_limit])

    async def async_discharge(self, power: int, soc_limit: int = 5, max_power: int = 800) -> dict:
        """
        Discharge battery in real-time control mode.
        Register 47015: [state=2, power, soc_limit]
        """
        clamped_power = min(power, max_power)
        _LOGGER.info(f"Discharging battery: {clamped_power}W, SOC limit: {soc_limit}%")
        return await self.set_data(16, 47015, [2, clamped_power, soc_limit])

    async def async_stop(self) -> dict:
        """
        Stop charging/discharging (standby mode).
        Register 47015: [state=0, 0, 0]
        """
        _LOGGER.info("Stopping battery (standby mode)")
        return await self.set_data(16, 47015, [0, 0, 0])

    # ==================== Advanced Control Functions (Gen 2) ====================
    async def async_set_max_ac_output_power(self, power: int) -> dict:
        """
        Set max AC output power (Register 1147).
        Gen 2 only.
        """
        _LOGGER.info(f"Setting max AC output power to {power}W")
        return await self.set_data(16, 1147, [power])

    async def async_set_feed_in_limit(self, power: int) -> dict:
        """
        Set feed-in power limit (Register 1146).
        Gen 2 only.
        """
        _LOGGER.info(f"Setting feed-in power limit to {power}W")
        return await self.set_data(16, 1146, [power])

    async def async_set_grid_charging(self, enable: bool) -> dict:
        """
        Enable/disable grid charging (Register 1143).
        0: Disable, 1: Enable
        Gen 2 only.
        """
        value = 1 if enable else 0
        _LOGGER.info(f"{'Enabling' if enable else 'Disabling'} grid charging")
        return await self.set_data(16, 1143, [value])

    async def async_set_inverter_input_limit(self, power: int) -> dict:
        """
        Set inverter input limit (Register 1138).
        Gen 2 only.
        """
        _LOGGER.info(f"Setting inverter input limit to {power}W")
        return await self.set_data(16, 1138, [power])

    async def async_set_bypass(self, enable: bool) -> dict:
        """
        Enable/disable bypass (Register 7266).
        0: Disable, 1: Enable
        Gen 2 only.
        """
        value = 1 if enable else 0
        _LOGGER.info(f"{'Enabling' if enable else 'Disabling'} bypass")
        return await self.set_data(16, 7266, [value])

    async def async_set_backup_soc(self, soc: int) -> dict:
        """
        Set backup SOC percentage (Register 1142).
        Gen 2 only.
        """
        _LOGGER.info(f"Setting backup SOC to {soc}%")
        return await self.set_data(16, 1142, [soc])

    async def async_set_light(self, enable: bool) -> dict:
        """
        Enable/disable light (Register 7265).
        0: Disable, 1: Enable
        Gen 2 only.
        """
        value = 1 if enable else 0
        _LOGGER.info(f"{'Enabling' if enable else 'Disabling'} light")
        return await self.set_data(16, 7265, [value])

    # ==================== System Information ====================
    async def async_get_system_info(self) -> Dict[str, Any]:
        """
        Get CMS (Communication Management System) information.
        Uses Sys.GetConfig endpoint.
        """
        try:
            async with self.session.get(
                f"{self.base_url}/Sys.GetConfig", 
                timeout=aiohttp.ClientTimeout(total=15)
            ) as resp:
                if resp.status == 200:
                    return await resp.json()
                else:
                    _LOGGER.error(f"Failed to get system info: HTTP {resp.status}")
                    return {}
        except Exception as e:
            _LOGGER.error(f"Error getting system info: {e}")
            return {}
