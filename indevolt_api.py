import asyncio, aiohttp, json
from typing import Dict, Any, List

class IndevoltAPI:
    def __init__(self, host: str, port: int, session: aiohttp.ClientSession):
        self.host, self.port, self.session = host, port, session
        self.base_url = f"http://{host}:{port}/rpc"

    async def fetch_data(self, keys: List[int]) -> Dict[str, Any]:
        """Fetch data from specific registers."""
        config = json.dumps({"t": keys}).replace(" ", "")
        async with self.session.post(f"{self.base_url}/Indevolt.GetData?config={config}", timeout=15) as resp:
            return await resp.json() if resp.status == 200 else {}

    async def set_data(self, f: int, t: int, v: list) -> dict:
        """Write data to registers."""
        config = json.dumps({"f": f, "t": t, "v": v}).replace(" ", "")
        async with self.session.post(f"{self.base_url}/Indevolt.SetData?config={config}", timeout=15) as resp:
            return await resp.json()

    async def async_charge(self, p, s=100, m=1200):
        """Set to Real-Time Mode then Charge (Register 47015: State 1)."""
        # Note: Ideally switch to Mode 4 first, but this command handles the charge action
        return await self.set_data(16, 47015, [1, min(p, m), s])

    async def async_discharge(self, p, s=5, m=800):
        """Set to Real-Time Mode then Discharge (Register 47015: State 2)."""
        return await self.set_data(16, 47015, [2, min(p, m), s])

    async def async_stop(self):
        """Stop charging/discharging (Register 47015: State 0)."""
        return await self.set_data(16, 47015, [0, 0, 0])

    async def async_set_mode(self, mode: int):
        """
        Set the device working mode (Register 47005).
        1: Self-consumed prioritized
        2: Charge/Discharge Schedule
        4: Real-time control
        """
        return await self.set_data(16, 47005, [mode])

    async def async_set_backup_soc(self, soc: int):
        """
        Set Backup SOC (minimum reserve SOC).
        Register: 1142
        Valid range: 5–100
        """
        soc = int(soc)
        if soc < 5 or soc > 100:
            raise ValueError("Backup SOC must be between 5 and 100")

        return await self.set_data(16, 1142, [soc])
        
    async def async_set_ac_output_power(self, ac_output_power: int):
        """
        Set AC Output Power.
        Register: 1147
        Valid range: 0–2400
        """
        ac_output_power = int(ac_output_power)
        if ac_output_power < 0 or ac_output_power > 2400:
            raise ValueError("AC Output power must be between 50 and 2400")

        return await self.set_data(16, 1147, [ac_output_power]) 
        
    async def async_set_feed_in_power(self, feed_in_power: int):
        """
        Set Feed-In Power.
        Register: 1146
        Valid range: 0–2400
        """
        feed_in_power = int(feed_in_power)
        if feed_in_power < 0 or feed_in_power > 2400:
            raise ValueError("Feed-In power must be between 50 and 2400")

        return await self.set_data(16, 1146, [feed_in_power]) 
        
    async def async_set_grid_charging(self, grid_charging: int):
        """
        Enable/Disable Grid Charging.
        Register: 1143
        Value: 0/1
        """
        grid_charging = int(grid_charging)

        return await self.set_data(16, 1143, [grid_charging]) 
        
    async def async_set_inverter_input_power(self, inverter_input_power: int):
        """
        Set Inverter Input Power.
        Register: 1138
        Valid range: 0–2400
        """
        inverter_input_power = int(inverter_input_power)
        if inverter_input_power < 0 or inverter_input_power > 2400:
            raise ValueError("Inverter Input power must be between 0 and 2400")

        return await self.set_data(16, 1138, [inverter_input_power])         
        
    async def async_set_bypass_socket(self, bypass_socket: int):
        """
        Enable/Disable Bypass Socket.
        Register: 7266
        Value: 0/1
        """
        bypass_socket = int(bypass_socket)

        return await self.set_data(16, 7266, [bypass_socket])
        
    async def async_set_led_light(self, led_light: int):
        """
        Enable/Disable LED Light.
        Register: 7265
        Value: 0/1
        """
        led_light = int(led_light)

        return await self.set_data(16, 7265, [led_light])
