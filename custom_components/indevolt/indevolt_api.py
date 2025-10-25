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
        self.timeout = aiohttp.ClientTimeout(total=60)
    
    async def fetch_data(self, keys: List[int]) -> Dict[str, Any]:
        """Fetch raw JSON data from the device"""
        # KORREKTUR: keys ist jetzt List[int]
        config_param = json.dumps({"t": keys}).replace(" ", "")
        url = f"{self.base_url}/Indevolt.GetData?config={config_param}"
        
        try:
            async with self.session.post(url, timeout=self.timeout) as response:
                if response.status != 200:
                    raise Exception(f"HTTP status error: {response.status}")
                # Die API gibt Keys als Strings zurück, was für HA korrekt ist.
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

    # --- NEUE WARTBARE METHODEN (Optimierung 3) ---
    
    async def async_set_realtime_mode(self) -> dict[str, Any]:
        """Set the device to real-time control mode (Mode 4)."""
        # API-Referenz: f=16, t=47005, v=[4]
        return await self.set_data(f=16, t=47005, v=[4])

    async def async_charge(self, power: int) -> dict[str, Any]:
        """Send command to charge the battery."""
        # API-Referenz: f=16, t=47015, v=[1 (Charge), power, 100 (Timeout?)]
        return await self.set_data(f=16, t=47015, v=[1, power, 100])

    async def async_discharge(self, power: int) -> dict[str, Any]:
        """Send command to discharge the battery."""
        # API-Referenz: f=16, t=47015, v=[2 (Discharge), power, 5 (Timeout?)]
        return await self.set_data(f=16, t=47015, v=[2, power, 5])

    async def async_stop(self) -> dict[str, Any]:
        """Send command to stop charge/discharge."""
        # API-Referenz: f=16, t=47015, v=[0 (Stop), 0, 0]
        return await self.set_data(f=16, t=47015, v=[0, 0, 0])
