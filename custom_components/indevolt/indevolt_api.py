import asyncio, aiohttp, json
from typing import Dict, Any, List

class IndevoltAPI:
    def __init__(self, host: str, port: int, session: aiohttp.ClientSession):
        self.host, self.port, self.session = host, port, session
        self.base_url = f"http://{host}:{port}/rpc"

    async def fetch_data(self, keys: List[int]) -> Dict[str, Any]:
        config = json.dumps({"t": keys}).replace(" ", "")
        async with self.session.post(f"{self.base_url}/Indevolt.GetData?config={config}", timeout=15) as resp:
            return await resp.json() if resp.status == 200 else {}

    async def set_data(self, f: int, t: int, v: list) -> dict:
        config = json.dumps({"f": f, "t": t, "v": v}).replace(" ", "")
        async with self.session.post(f"{self.base_url}/Indevolt.SetData?config={config}", timeout=15) as resp:
            return await resp.json()

    async def async_charge(self, p, s=100, m=1200):
        return await self.set_data(16, 47015, [1, min(p, m), s])

    async def async_discharge(self, p, s=5, m=800):
        return await self.set_data(16, 47015, [2, min(p, m), s])

    async def async_stop(self):
        return await self.set_data(16, 47015, [0, 0, 0])
