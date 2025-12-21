import asyncio
import aiohttp
import json
from typing import Dict, Any, List

class IndevoltAPI:
    def __init__(self, host: str, port: int, session: aiohttp.ClientSession):
        self.host, self.port, self.session = host, port, session
        self.base_url = f"http://{host}:{port}/rpc"
        self.timeout = aiohttp.ClientTimeout(total=15)
    
    async def fetch_data(self, keys: List[int]) -> Dict[str, Any]:
        config_param = json.dumps({"t": keys}).replace(" ", "")
        url = f"{self.base_url}/Indevolt.GetData?config={config_param}"
        async with self.session.post(url, timeout=self.timeout) as resp:
            if resp.status != 200: raise Exception(f"HTTP error: {resp.status}")
            return await resp.json()

    async def set_data(self, f: int, t: int, v: list) -> dict[str, Any]:
        config_param = json.dumps({"f": f, "t": t, "v": v}).replace(" ", "")
        url = f"{self.base_url}/Indevolt.SetData?config={config_param}"
        async with self.session.post(url, timeout=self.timeout) as resp:
            if resp.status != 200: raise Exception(f"HTTP error: {resp.status}")
            return await resp.json()

    # New Working Mode Features
    async def async_set_working_mode(self, mode: int) -> dict[str, Any]:
        """Set working mode: 1=Self-Consumption, 2=Schedule, 4=Real-Time."""
        return await self.set_data(f=16, t=47005, v=[mode])

    async def async_charge(self, power: int, soc_limit: int = 100) -> dict[str, Any]:
        return await self.set_data(f=16, t=47015, v=[1, power, soc_limit])

    async def async_discharge(self, power: int, soc_limit: int = 5) -> dict[str, Any]:
        return await self.set_data(f=16, t=47015, v=[2, power, soc_limit])

    async def async_stop(self) -> dict[str, Any]:
        return await self.set_data(f=16, t=47015, v=[0, 0, 0])
