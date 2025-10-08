## QmdevHA (HACS Custom Integration) — Using Events

QmdevHA exposes Home Assistant events from ZMQ messages. Instead of directly controlling devices, you create automations that react to these events. This keeps logic in Home Assistant, making it flexible and extensible.

### Events

- qmdevha_key_event
  - qid: queue id (number)
  - key: key code (number, e.g., 0x13 = 19)
  - isrelease: whether the key is released (true/false)
  - timestamp: event timestamp (float)

- qmdevha_pack_event
  - onoff: power state (true/false)
  - timestamp: event timestamp (float)

### Example: Control a light on key release

```yaml
# configuration.yaml
automation:
  - alias: "QmdevHA key controls light"
    trigger:
      - platform: event
        event_type: qmdevha_key_event
        event_data:
          qid: 9
          key: 19  # 0x13
    condition:
      - condition: template
        value_template: "{{ trigger.event.data.isrelease }}"
    action:
      - service: light.turn_on
        target:
          entity_id: light.living_room
```

### Example: AC mode from pack event

```yaml
# configuration.yaml
automation:
  - alias: "QmdevHA pack controls AC"
    trigger:
      - platform: event
        event_type: qmdevha_pack_event
    action:
      - choose:
          - conditions:
              - condition: template
                value_template: "{{ trigger.event.data.onoff }}"
            sequence:
              - service: climate.set_hvac_mode
                target:
                  entity_id: climate.living_room_ac
                data:
                  hvac_mode: cool
          - conditions:
              - condition: template
                value_template: "{{ not trigger.event.data.onoff }}"
            sequence:
              - service: climate.set_hvac_mode
                target:
                  entity_id: climate.living_room_ac
                data:
                  hvac_mode: off
```

### Example: Scene and notification

```yaml
# configuration.yaml
automation:
  - alias: "QmdevHA scene trigger"
    trigger:
      - platform: event
        event_type: qmdevha_pack_event
        event_data:
          onoff: true
    action:
      - service: scene.turn_on
        target:
          entity_id: scene.movie_mode
      - service: notify.mobile_app_your_phone
        data:
          title: "QmdevHA"
          message: "Movie mode activated"
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