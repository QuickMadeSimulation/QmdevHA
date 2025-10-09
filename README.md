## QmdevHA (HACS Custom Integration) — Using Events

QmdevHA exposes Home Assistant events from [QuickMadeSimulation Flight Simulation Hardware](https://x-plane.vip/quickmade/shop/), it requires:

* Qmdev 7.1 or above, for X-Plane 11/12
* QmdevSimConnect 5.1 or above, for MSFS 2020/2024

Instead of directly controlling devices, you create automations that react to these events. This keeps logic in Home Assistant, making it flexible and extensible.

## Video Demo

https://youtube.com/shorts/vNuspspNrWk?si=Gh9OoM24CEk18FPi

## Installation

### Via HACS (Recommended): [HACS](https://hacs.xyz/)

One-click installation from HACS:

[![Open your Home Assistant instance and open the QmdevHA integration inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=QuickMadeSimulation&repository=QmdevHA&category=integration)

Or, HACS > In the search box, type **QmdevHA** > Click **QmdevHA**, getting into the detail page > DOWNLOAD


### Manual Installation

1. Copy the `custom_components/qmdevha` folder to your `custom_components` directory
2. Restart Home Assistant


### Events

- qmdevha_key_event
  - qid: quickmade device id (number)
  - key: key code (number, e.g., 0x13 = 19)
  - isrelease: whether the key is released (true/false)
  - timestamp: event timestamp (float)

- qmdevha_pack_event
  - onoff: power state (true/false)
  - timestamp: event timestamp (float)

### Example: Control a light on key release

```yaml
alias: QmdevHA DOME BRT
description: ""
triggers:
  - event_type: qmdevha_key_event
    event_data:
      qid: 9
      key: 18
    trigger: event
conditions: []
actions:
  - if:
      - condition: template
        value_template: "{{ trigger.event.data.isrelease }}"
    then:
      - action: switch.turn_off
        target:
          entity_id: switch.zimi_cn_1021898767_dhkg01_on_p_2_1
        data: {}
    else:
      - action: switch.turn_on
        metadata: {}
        data: {}
        target:
          entity_id: switch.zimi_cn_1021898767_dhkg01_on_p_2_1
```

```yaml
alias: QmdevHA DOME DIM
description: ""
triggers:
  - event_type: qmdevha_key_event
    event_data:
      qid: 9
      key: 19
    trigger: event
conditions: []
actions:
  - if:
      - condition: template
        value_template: "{{ trigger.event.data.isrelease }}"
    then:
      - action: switch.turn_on
        metadata: {}
        data: {}
        target:
          entity_id: switch.giot_cn_1163257474_v8icm_on_p_2_1
    else:
      - action: switch.turn_off
        target:
          entity_id: switch.giot_cn_1163257474_v8icm_on_p_2_1
        data: {}

```

### Example: AC mode from pack event

```yaml
# configuration.yaml
alias: QmdevHA pack controls AC
description: ""
triggers:
  - event_type: qmdevha_pack_event
    trigger: event
conditions: []
actions:
  - if:
      - condition: template
        value_template: "{{ trigger.event.data.onoff }}"
    then:
      - sequence:
          - service: climate.set_temperature
            data:
              temperature: |
                {{ trigger.event.data.degree | float }}
              hvac_mode: auto
            target:
              entity_id: climate.210006721135374_climate
    else:
      - sequence:
          - service: climate.set_hvac_mode
            entity_id: climate.210006721135374_climate
            data:
              hvac_mode: off

```

