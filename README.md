# Home Assistant Indevolt Integration (with Control Services)

This is a modified version of the original [homeassistant-indevolt](https://github.com/solarmanpv/homeassistant-indevolt) custom integration.  
**This fork adds essential control services and expanded configuration options**, allowing users to actively manage their Indevolt battery (e.g., PowerFlex 2000, BK1600) directly from Home Assistant and tune behavior for zero-export, charge/discharge limits, and safety constraints.

This README documents the features and options included in the 1.0.3 release.

---

## Release: 1.0.3 — Summary / Changelog

Highlights in 1.0.3:
- Added additional configuration options (enable_control_services, realtime_on_start, max charge/discharge limits, deadband tuning, meter entity mapping).
- Extended services: charge/discharge now accept optional duration and target_soc parameters; stop is unchanged.
- Added new sensors for finer telemetry (string-level DC data, battery temperature, firmware version, serial).
- Improved real-time mode handling: optional automatic enable on HA startup and a safer handshake with retries.
- Better error handling and visible status sensor for control command results.
- Manifest bumped to 1.0.3.

Full changelog:
- Feature: enable/disable control services from config.
- Feature: automatic set_realtime_mode on Home Assistant start (config option).
- Feature: charge/discharge service parameters: power (W), duration (seconds/minutes, optional), target_soc (%) (optional).
- Feature: new sensors (battery_temperature, firmware_version, serial_number, dc_string_currents, dc_string_voltages).
- Improvement: configurable max_charge_power / max_discharge_power enforced by integration (prevents sending commands above device limits).
- Improvement: configurable grid deadband to tune zero-export automations.
- Improvement: status sensor indevolt.control_status with last_command and last_result.
- Fix: retry logic for entering realtime mode (useful after device reboot).

---

## Supported Devices

This integration has been tested and confirmed to work with the following device models:

- **Gen 1:** BK1600 / BK1600Ultra
- **Gen 2:** SolidFlex / PowerFlex2000

The integration will automatically provide the correct sensors based on the device model you select during setup.

---

## Features & Services

This fork provides a set of services in the `indevolt` domain and additional configuration options to control and monitor Indevolt devices.

### indevolt.set_realtime_mode
Puts the device into a mode that accepts real-time control commands. For reliable operation of charge, discharge, and stop, this service should be called once after Home Assistant starts unless you enabled the automatic realtime_on_start option.

Parameters:
- timeout (optional, integer): how long (in seconds) the device will remain in realtime mode before the integration will automatically refresh the session. Default: integration internal default.
- retry (optional, integer): number of retries if the device doesn't accept the mode immediately.

Example:
```yaml
service: indevolt.set_realtime_mode
data:
  timeout: 3600
  retry: 3
```

---

### indevolt.charge
Tells the battery to start charging from the grid or surplus solar.

Parameters:
- power (required, integer): Charging power in Watts (positive integer).
- duration (optional, integer): Charging duration in seconds. If omitted, charge until stopped or target_soc reached.
- target_soc (optional, integer 0-100): Stop charging when battery SOC reaches this value.
- priority (optional, string): "eco" | "normal" | "fast" — integration may cap power depending on selected priority.

Notes:
- The integration will clamp the requested power to the configured max_charge_power if set.

Example:
```yaml
service: indevolt.charge
data:
  power: 1500
  target_soc: 85
  duration: 3600
```

---

### indevolt.discharge
Tells the battery to start discharging to power your home.

Parameters:
- power (required, integer): Discharging power in Watts (positive integer).
- duration (optional, integer): Discharging duration in seconds.
- target_soc (optional, integer 0-100): Stop discharging when battery SOC falls to this value.
- priority (optional, string): "eco" | "normal" | "burst".

Notes:
- The integration will clamp the requested power to the configured max_discharge_power if set.

Example:
```yaml
service: indevolt.discharge
data:
  power: 1200
  target_soc: 25
```

---

### indevolt.stop
Puts the battery into standby mode, stopping any active charging or discharging.

Parameters: none

Example:
```yaml
service: indevolt.stop
data: {}
```

---

## New/Updated Configuration Options

You can configure these options via the integration config flow or YAML (if using YAML setup). The config flow will prefer typed inputs and validation.

- Host: The IP address of your Indevolt device.
- Port: The port for the API (default: `8080`).
- Scan Interval: How often to poll the device for data (default: `30` seconds). Accepts integer seconds.
- Device Model: Select your specific model from the dropdown list (important for correct sensors).
- enable_control_services: boolean (default: true) — enable or disable charge/discharge/stop services.
- realtime_on_start: boolean (default: false) — automatically invoke set_realtime_mode on Home Assistant start.
- max_charge_power: integer (Watts, optional) — maximum charge limit enforced by the integration.
- max_discharge_power: integer (Watts, optional) — maximum discharge limit enforced by the integration.
- default_deadband: integer (Watts, default 50) — recommended deadband for zero-export controllers.
- meter_entity_id: string (entity_id, optional) — if you have an external meter, map it here for use by automations and default templates.
- safety_soc_min: integer (0-100, optional) — lowest SOC allowed for automatic discharging.
- safety_soc_max: integer (0-100, optional) — highest SOC allowed for automatic charging.

When set via the config flow, the integration validates values and the device response.

---

## Available Sensors

This integration creates a comprehensive set of sensor entities to monitor your device. New in 1.0.3 are additional telemetry sensors for better insight and safer automation logic.

Power / Energy:
- sensor.indevolt_total_ac_output_power
- sensor.indevolt_battery_power
- sensor.indevolt_meter_power (if meter_entity_id not provided)
- sensor.indevolt_daily_production
- sensor.indevolt_total_production

Battery:
- sensor.indevolt_total_battery_soc
- sensor.indevolt_battery_state (charging / discharging / idle)
- sensor.indevolt_battery_temperature (new)
- sensor.indevolt_battery_remaining_time (estimated)

String / Input:
- sensor.indevolt_dc_string_1_current (new, where applicable)
- sensor.indevolt_dc_string_1_voltage (new)
- sensor.indevolt_dc_string_2_current (new)
- sensor.indevolt_dc_string_2_voltage (new)

Device Info / Status:
- sensor.indevolt_firmware_version (new)
- sensor.indevolt_serial_number (new)
- sensor.indevolt_working_mode
- sensor.indevolt_meter_connection_status
- sensor.indevolt.control_status (new) — shows last control command result and timestamp

Notes:
- Exact sensor names depend on model and device capabilities.

---

## Automation Examples

### 1. Enable Real-Time Control on Startup (automatically via config or automation)
If you did not enable realtime_on_start in the config, use this automation to ensure the device will accept control commands:

```yaml
alias: "Indevolt: Enable Real-Time Control on Startup"
description: "Sets the Indevolt device to real-time mode for control services."
trigger:
  - platform: homeassistant
    event: start
action:
  - service: indevolt.set_realtime_mode
    data:
      timeout: 3600
      retry: 3
mode: single
```

### 2. Zero-Export Controller (Nulleinspeisung) — updated to use new params
This controller uses a grid power sensor to keep import/export near zero, respects deadband, and uses target_soc to avoid overcharging.

```yaml
alias: Battery Zero-Export Controller
description: Dynamically controls the battery to achieve zero grid export.
mode: restart

trigger:
  - platform: time_pattern
    seconds: "/30"
  - platform: state
    entity_id: sensor.your_grid_power_sensor
  - platform: state
    entity_id: binary_sensor.your_ev_charging_sensor

action:
  - if:
      - condition: state
        entity_id: binary_sensor.your_ev_charging_sensor
        state: "on"
    then:
      - service: indevolt.stop
        data: {}
    else:
      - variables:
          grid_power: "{{ states('sensor.your_grid_power_sensor') | float(0) }}"
          battery_power: "{{ states('sensor.indevolt_battery_power') | float(0) }}"
          deadband: "{{ states('input_number.grid_power_deadband') | float(50) }}"
          min_soc: "{{ states('input_number.battery_minimum_soc') | int(20) }}"
          max_soc: "{{ states('input_number.battery_maximum_soc') | int(90) }}"
          soc: "{{ states('sensor.indevolt_total_battery_soc') | float(0) }}"
          max_charge: "{{ state_attr('config_entry', 'max_charge_power') | default(3000) }}"
          max_discharge: "{{ state_attr('config_entry', 'max_discharge_power') | default(3000) }}"

      - choose:
          - conditions:
              - "{{ grid_power < -deadband }}"
              - "{{ soc < max_soc }}"
            sequence:
              - service: indevolt.charge
                data:
                  power: "{{ [ (battery_power + grid_power) | abs | int, max_charge ] | min}}"
                  target_soc: "{{ max_soc }}"
          - conditions:
              - "{{ grid_power > deadband }}"
              - "{{ soc > min_soc }}"
            sequence:
              - service: indevolt.discharge
                data:
                  power: "{{ [ (battery_power + grid_power) | int, max_discharge ] | min }}"
                  target_soc: "{{ min_soc }}"
        default:
          - service: indevolt.stop
            data: {}
```

### 3. Charge for a fixed duration (new duration param)
```yaml
service: indevolt.charge
data:
  power: 2000
  duration: 1800
```

---

## Status & Troubleshooting

- Control commands (charge/discharge/stop) will be reflected in `sensor.indevolt.control_status` which includes the last command, parameters, and result code from the device.
- If commands fail, confirm the device is in realtime mode. Use the `indevolt.set_realtime_mode` service and check the status sensor.
- If the integration is not creating expected sensors, double-check Device Model in the integration options and restart Home Assistant.

---

## Manifest

```json
{
  "domain": "indevolt",
  "name": "INDEVOLT",
  "version": "1.0.3",
  "requirements": ["aiohttp"],
  "dependencies": [],
  "codeowners": [],
  "config_flow": true,
  "iot_class": "local_polling"
}
```

---

## Installation

1. Download the zip for this release and copy the files to /config/custom_components/indevolt/
2. In Home Assistant, go to **Settings > Devices & Services**.
3. Click **Add Integration** and search for `INDEVOLT`.
4. Enter the required information and tune the optional settings described above.

---

## Credits

Based on the work by [solarmanpv/homeassistant-indevolt](https://github.com/solarmanpv/homeassistant-indevolt).