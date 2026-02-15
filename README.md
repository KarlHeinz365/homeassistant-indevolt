# Updated Indevolt Integration from Speedy2524 (Sensors, Services, API calls, Error handling, Bug fixing)

**- Extended Sensor.py with about ~180 sensor/entities total**

**- Extended Services (Setting Backup SOC, Setting AC Output Power Limit, Setting Feed-In Power Limit, Enable/Disable Grid Charging, Setting Inverter Input Power, Enable/Disable Bypass Socket, Enable/Disable LED Light)**

**- Modified API calls (Batch processing to handle large sensor list queries)**

**- Modified Error handling**

**- Fixed some bugs**

---
---
---

# Home Assistant Indevolt Integration (with Control Services)

This is a modified version of the original [homeassistant-indevolt](https://github.com/solarmanpv/homeassistant-indevolt) custom integration.  
**This fork adds essential control services**, allowing users to actively manage their Indevolt battery (e.g., PowerFlex 2000, BK1600) directly from Home Assistant.

The original integration provides excellent sensor data for monitoring, but lacks the ability to send commands.  
**This version bridges that gap** by implementing services to start charging, start discharging, and stop the battery, making it possible to create advanced automations like a zero-export (Nulleinspeisung) controller.

---

## Supported Devices

This integration has been tested and confirmed to work with the following device models:

- **Gen 1:** BK1600 / BK1600Ultra
- **Gen 2:** SolidFlex / PowerFlex2000

The integration will automatically provide the correct sensors based on the device model you select during setup.

---

## Features & Services

This fork adds the following custom services to the `indevolt` domain, which can be used in your automations and scripts:

### `indevolt.set_realtime_mode`
> Puts the device into a mode that accepts real-time control commands.  
> For reliable operation of charge, discharge, and stop, this service should be called **once after Home Assistant starts**.

| Parameter | Required | Description                       |
|-----------|----------|-----------------------------------|
| (none)    | –        | Puts the device in real-time mode |

---

### `indevolt.charge`
> Tells the battery to start charging from the grid or surplus solar.

| Parameter | Required | Description                  | Example |
|-----------|----------|------------------------------|---------|
| power     | Yes      | Charging power in Watts      | 500     |

---

### `indevolt.discharge`
> Tells the battery to start discharging to power your home.

| Parameter | Required | Description                    | Example |
|-----------|----------|--------------------------------|---------|
| power     | Yes      | Discharging power in Watts     | 300     |

---

### `indevolt.stop`
> Puts the battery into standby mode, stopping any active charging or discharging.

| Parameter | Required | Description                       |
|-----------|----------|-----------------------------------|
| (none)    | –        | Halts current charge/discharge    |

---

## Available Sensors

The integration creates a rich set of sensor entities to monitor every aspect of your device, including:

- **Power Sensors:** DC Input Power (per string), Total AC Output Power, Battery Power, Meter Power
- **Energy Sensors:** Daily Production, Cumulative Production, Battery Daily/Total Charging & Discharging Energy
- **Battery Sensors:** Battery SOC (State of Charge), Battery Charge/Discharge State
- **Status Sensors:** Working Mode, Meter Connection Status

---

## Configuration

For Installation add the repository in HACS as a Integration or
1. **Install** this custom component download the zip and put all files in /homeassistant/custom_components/indevolt/
2. In Home Assistant, go to **Settings > Devices & Services**.
3. Click **Add Integration** and search for `INDEVOLT`.
4. Enter the required information:
    - **Host:** The IP address of your Indevolt device.
    - **Port:** The port for the API (default: `8080`).
    - **Scan Interval:** How often to poll the device for data (default: `30` seconds).
    - **Device Model:** Select your specific model from the dropdown list.  
      _This is important for loading the correct sensors._

---

## Automation Examples

### 1. Enable Real-Time Control on Startup

This essential automation ensures your device is ready to receive commands whenever Home Assistant is running.

```yaml
alias: "Indevolt: Enable Real-Time Control on Startup"
description: "Sets the Indevolt device to real-time mode for control services."
trigger:
  - platform: homeassistant
    event: start
action:
  - service: indevolt.set_realtime_mode
mode: single
```

---

### 2. Zero-Export Controller (Nulleinspeisung)

This is the primary use case for these new services. The following automation uses a grid power sensor to keep the import/export near zero. It dynamically charges the battery with surplus solar power and discharges it to cover home consumption, minimizing grid interaction.

```yaml
alias: Battery Zero-Export Controller
description: Dynamically controls the battery to achieve zero grid export.
mode: restart

trigger:
  # Trigger periodically to ensure the system is always adjusting.
  - platform: time_pattern
    seconds: "/30"
  # Trigger immediately on any change in grid power.
  - platform: state
    entity_id: sensor.your_grid_power_sensor # e.g., sensor.fronius_power_grid
  # (Optional) Trigger on EV charging state changes to pause the controller.
  - platform: state
    entity_id: binary_sensor.your_ev_charging_sensor # e.g., binary_sensor.wallbox_status

action:
  # First, check for any overriding conditions, like EV charging.
  - if:
      - condition: state
        entity_id: binary_sensor.your_ev_charging_sensor
        state: "on"
    then:
      # If the override is active, stop the battery and exit the automation.
      - service: indevolt.stop
        data: {}
    else:
      # If no overrides are active, proceed with the main control logic.
      # 1. Define variables to make the logic clean and readable.
      - variables:
          grid_power: "{{ states('sensor.your_grid_power_sensor') | int(0) }}"
          # IMPORTANT: Adjust this entity_id to your battery's power sensor!
          battery_power: "{{ states('sensor.indevolt_battery_power') | int(0) }}"
          deadband: "{{ states('input_number.grid_power_deadband') | int(0) }}"
          min_soc: "{{ states('input_number.battery_minimum_soc') | int(0) }}"
          max_soc: "{{ states('input_number.battery_maximum_soc') | int(0) }}"
          soc: "{{ states('sensor.indevolt_total_battery_soc') | int(0) }}"

      # 2. Use a 'choose' action to implement the core control logic.
      - choose:
          # RULE 1: GRID EXPORT (SURPLUS POWER) -> CHARGE BATTERY
          - conditions:
              # Condition: Exporting more power than the deadband allows (negative value).
              - "{{ grid_power < -deadband }}"
              # Condition: Battery is not yet full.
              - "{{ soc < max_soc }}"
            sequence:
              - service: indevolt.charge
                data:
                  # New Power = Current Battery Power + Grid Export
                  power: "{{ (battery_power + grid_power) | abs | int }}"

          # RULE 2: GRID IMPORT -> DISCHARGE BATTERY
          - conditions:
              # Condition: Importing more power than the deadband allows (positive value).
              - "{{ grid_power > deadband }}"
              # Condition: Battery is above the minimum allowed SOC.
              - "{{ soc > min_soc }}"
            sequence:
              - service: indevolt.discharge
                data:
                  # New Power = Current Battery Power + Grid Import
                  power: "{{ (battery_power + grid_power) | int }}"

        # DEFAULT ACTION: GRID POWER IS WITHIN THE DEADBAND -> STOP BATTERY
        default:
          - service: indevolt.stop
            data: {}
```

---

## Manifest

```json
{
  "domain": "indevolt",
  "name": "INDEVOLT",
  "version": "1.0",
  "requirements": ["aiohttp"],
  "dependencies": [],
  "codeowners": [],
  "config_flow": true,
  "iot_class": "local_polling"
}
```

---

## Credits

Based on the work by [solarmanpv/homeassistant-indevolt](https://github.com/solarmanpv/homeassistant-indevolt).

---
