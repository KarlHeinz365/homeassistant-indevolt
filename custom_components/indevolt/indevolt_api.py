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
        url = f"{self.base_url}/Indevolt.GetData?config={json.dumps({'t': keys}).replace(' ', '')}"
        async with self.session.post(url, timeout=self.timeout) as r:
            return await r.json()

    async def set_data(self, f: int, t: int, v: list) -> dict[str, Any]:
        url = f"{self.base_url}/Indevolt.SetData?config={json.dumps({'f': f, 't': t, 'v': v}).replace(' ', '')}"
        async with self.session.post(url, timeout=self.timeout) as r:
            return await r.json()

    # CONTROL MODES
    async def async_set_self_consumption_mode(self):
        """Set Mode 1 (Self-consumed prioritized)."""
        return await self.set_data(f=16, t=47005, v=[1])

    async def async_set_schedule_mode(self):
        """Set Mode 2 (Charge/discharge Schedule)."""
        return await self.set_data(f=16, t=47005, v=[2])

    async def async_set_realtime_mode(self):
        """Set Mode 4 (Real-time control)."""
        return await self.set_data(f=16, t=47005, v=[4])

    async def async_charge(self, power, soc_limit=100, max_power=1200):
        return await self.set_data(f=16, t=47015, v=[1, min(power, max_power), soc_limit])

    async def async_discharge(self, power, soc_limit=5, max_power=800):
        return await self.set_data(f=16, t=47015, v=[2, min(power, max_power), soc_limit])

    async def async_stop(self):
        return await self.set_data(f=16, t=47015, v=[0, 0, 0])
