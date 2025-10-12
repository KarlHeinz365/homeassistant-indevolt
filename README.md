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

1. **Install** this custom component (e.g., via HACS).
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
alias: "Batterie Nulleinspeisung Steuerung (Indevolt)"
description: "Steuert die Batterie für Nulleinspeisung und Nachtversorgung."
mode: single

trigger:
  - platform: time_pattern
    seconds: "/30"
  - platform: state
    entity_id: sensor.your_grid_power_sensor        # e.g., sensor.power_grid
  - platform: state
    entity_id: binary_sensor.your_ev_charging_sensor # Optional: sensor to pause battery control

action:
  - choose:
      # RULE 1 (Optional): EV IS CHARGING -> STOP BATTERY
      - conditions:
          - condition: state
            entity_id: binary_sensor.your_ev_charging_sensor
            state: "on"
        sequence:
          - service: indevolt.stop
          - stop: "EV charging is active, pausing battery control."

      # RULE 2: SURPLUS POWER (EXPORTING) -> CHARGE BATTERY
      # Condition: Exporting more than the deadband value (e.g., 50W)
      - conditions:
          - condition: numeric_state
            entity_id: sensor.your_grid_power_sensor
            below: -50       # Negative value means export
          - condition: numeric_state
            entity_id: sensor.indevolt_total_battery_soc
            below: 99        # Don't charge if almost full
        sequence:
          - service: indevolt.charge
            data:
              power: "{{ states('sensor.your_grid_power_sensor') | int(0) | abs }}"

      # RULE 3: GRID IMPORT (CONSUMING) -> DISCHARGE BATTERY
      # Condition: Importing more than the deadband value (e.g., 50W)
      - conditions:
          - condition: numeric_state
            entity_id: sensor.your_grid_power_sensor
            above: 50        # Positive value means import
          - condition: numeric_state
            entity_id: sensor.indevolt_total_battery_soc
            above: 20        # Minimum SOC to allow discharging
        sequence:
          - service: indevolt.discharge
            data:
              power: "{{ states('sensor.your_grid_power_sensor') | int(0) }}"

    # DEFAULT ACTION: IN DEADBAND (-50W to 50W) -> STOP BATTERY
    default:
      - service: indevolt.stop
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
