import asyncio
import aiohttp
import json
from typing import Dict, Any, List

class IndevoltAPI:
    """Handles all HTTP communication with Indevolt devices"""
    
    def __init__(self, host: str, port: int, session: aiohttp.ClientSession):
        self.host = host
        self.port = port
        self.session = session
        self.base_url = f"http://{host}:{port}/rpc"
        self.timeout = aiohttp.ClientTimeout(total=15)  # Reduced from 60s for local devices
    
    async def fetch_data(self, keys: List[int]) -> Dict[str, Any]:
        """Fetch raw JSON data from the device"""
        config_param = json.dumps({"t": keys}).replace(" ", "")
        url = f"{self.base_url}/Indevolt.GetData?config={config_param}"
        
        try:
            async with self.session.post(url, timeout=self.timeout) as response:
                if response.status != 200:
                    raise Exception(f"HTTP status error: {response.status}")
                # API returns keys as strings
                return await response.json()
                
        except asyncio.TimeoutError:
            raise Exception("Indevolt.GetData Request timed out")
        except aiohttp.ClientError as err:
            raise Exception(f"Indevolt.GetData Network error: {err}")

    async def set_data(self, f: int, t: int, v: list) -> dict[str, Any]:
        """Send raw JSON data to the device"""
        config_param = json.dumps({"f": f, "t": t, "v": v}).replace(" ", "")
        url = f"{self.base_url}/Indevolt.SetData?config={config_param}"
        
        try:
            async with self.session.post(url, timeout=self.timeout) as response:
                if response.status != 200:
                    raise Exception(f"HTTP status error: {response.status}")
                return await response.json()

        except asyncio.TimeoutError:
            raise Exception("Indevolt.SetData Request timed out")
        except aiohttp.ClientError as err:
            raise Exception(f"Indevolt.SetData Network error: {err}")

    # High-level control methods
    
    async def async_set_realtime_mode(self) -> dict[str, Any]:
        """Set the device to real-time control mode (Mode 4)."""
        return await self.set_data(f=16, t=47005, v=[4])

    async def async_charge(self, power: int, soc_limit: int = 100, max_power: int = 1200) -> dict[str, Any]:
        """Send command to charge the battery.
        
        Args:
            power: Charging power in Watts
            soc_limit: Stop charging when battery reaches this SOC% (0-100)
            max_power: Maximum allowed charging power (from config)
        """
        if not 0 <= power <= max_power:
            raise ValueError(f"Charging power must be 0-{max_power}W, got {power}W")
        if not 0 <= soc_limit <= 100:
            raise ValueError(f"SOC limit must be 0-100%, got {soc_limit}%")
        
        return await self.set_data(f=16, t=47015, v=[1, power, soc_limit])

    async def async_discharge(self, power: int, soc_limit: int = 5, max_power: int = 800) -> dict[str, Any]:
        """Send command to discharge the battery.
        
        Args:
            power: Discharging power in Watts
            soc_limit: Stop discharging when battery reaches this SOC% (0-100)
            max_power: Maximum allowed discharging power (from config)
        """
        if not 0 <= power <= max_power:
            raise ValueError(f"Discharging power must be 0-{max_power}W, got {power}W")
        if not 0 <= soc_limit <= 100:
            raise ValueError(f"SOC limit must be 0-100%, got {soc_limit}%")
        
        return await self.set_data(f=16, t=47015, v=[2, power, soc_limit])

    async def async_stop(self) -> dict[str, Any]:
        """Send command to stop charge/discharge (standby mode)."""
        return await self.set_data(f=16, t=47015, v=[0, 0, 0])
