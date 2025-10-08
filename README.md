## QmdevHA (HACS Custom Integration) — Using Events

QmdevHA exposes Home Assistant events from Qmdev 7.1/QmdevSimConnect 5.1. Instead of directly controlling devices, you create automations that react to these events. This keeps logic in Home Assistant, making it flexible and extensible.

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

### Debugging

Enable logs and inspect events in Developer Tools → Events.

```yaml
logger:
  default: info
  logs:
    custom_components.qmdevha: debug
```

Optional: log every QmdevHA event to the system log.

```yaml
automation:
  - alias: "Log QmdevHA events"
    trigger:
      - platform: event
        event_type: qmdevha_key_event
      - platform: event
        event_type: qmdevha_pack_event
    action:
      - service: system_log.write
        data:
          level: info
          message: "{{ trigger.event.event_type }}: {{ trigger.event.data }}"
```

### Best practices

- Filter with event_data to match only what you need
- Add safety conditions (entity availability, time, modes)
- Avoid heavy work in automations; call services quickly
- Log important actions for easier troubleshooting