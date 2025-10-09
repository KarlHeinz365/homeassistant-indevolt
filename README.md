# Home Assistant Indevolt Integration (with Control Services)

This is a modified version of the original [homeassistant-indevolt](https://github.com/solarmanpv/homeassistant-indevolt) custom integration. This fork adds essential control services, allowing users to actively manage their Indevolt battery (e.g., PowerFlex 2000) directly from Home Assistant.

The original integration provides excellent sensor data for monitoring, but lacks the ability to send commands. This version bridges that gap by implementing services to start charging, start discharging, and stop the battery, making it possible to create advanced automations like a zero-export (Nulleinspeisung) controller.

## Features Added

This fork adds the following custom services to the `indevolt` domain:

* **`indevolt.charge`**: Starts charging the battery with a specified power.
* **`indevolt.discharge`**: Starts discharging the battery with a specified power.
* **`indevolt.stop`**: Puts the battery into standby mode, stopping any active charging or discharging.

## Configuration

After installing this custom component, the new services will be available automatically. The `charge` and `discharge` services require a `power` parameter to be passed.

### Service: `indevolt.charge`

Tells the battery to start charging.

| Parameter | Required | Description                | Example |
| :-------- | :------- | :------------------------- | :------ |
| `power`   | Yes      | The charging power in Watts. | `500`   |

### Service: `indovolt.discharge`

Tells the battery to start discharging.

| Parameter | Required | Description                  | Example |
| :-------- | :------- | :--------------------------- | :------ |
| `power`   | Yes      | The discharging power in Watts. | `300`   |

### Service: `indevolt.stop`

Puts the battery into standby mode. It takes no parameters.

## Automation Example: Zero-Export Controller (Nulleinspeisung)

This is the primary use case for these new services. The following automation uses a grid power sensor to keep the import/export at zero, while also respecting an EV charger.

```yaml
alias: Batterie Nulleinspeisung Steuerung (Indevolt)
description: Steuert die Batterie für Nulleinspeisung und Nachtversorgung.
mode: single

trigger:
  - platform: time_pattern
    seconds: "/30"
  - platform: state
    entity_id: sensor.your_grid_power_sensor # e.g., sensor.power_grid_fronius_power_flow
  - platform: state
    entity_id: binary_sensor.your_ev_charging_sensor # e.g., binary_sensor.evcc_auto_ladt

action:
  - choose:
      # RULE 1: EV IS CHARGING -> STOP BATTERY
      - conditions:
          - condition: state
            entity_id: binary_sensor.your_ev_charging_sensor
            state: "on"
        sequence:
          - service: indevolt.stop

      # RULE 2: SURPLUS POWER -> CHARGE BATTERY
      - conditions:
          - condition: template
            value_template: "{{ states('sensor.your_grid_power_sensor') | float(0) < (-1 * states('input_number.netz_pufferzone') | float(0)) }}"
          - condition: numeric_state
            entity_id: sensor.indevolt_solidflex_powerflex2000_battery_soc
            below: 99
        sequence:
          - service: indevolt.charge
            data:
              power: "{{ states('sensor.your_grid_power_sensor') | int | abs }}"

      # RULE 3: GRID IMPORT -> DISCHARGE BATTERY
      - conditions:
          - condition: template
            value_template: "{{ states('sensor.your_grid_power_sensor') | float(0) > states('input_number.netz_pufferzone') | float(0)) }}"
          - condition: template
            value_template: "{{ states('sensor.indevolt_solidflex_powerflex2000_battery_soc') | float(0) > states('input_number.batterie_mindest_soc') | float(0) }}"
        sequence:
          - service: indevolt.discharge
            data:
              power: "{{ states('sensor.your_grid_power_sensor') | int }}"

    # DEFAULT ACTION: IN DEADBAND -> STOP BATTERY
    default:
      - service: indevolt.stop
