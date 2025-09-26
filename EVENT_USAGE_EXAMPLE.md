# QmdevHA 事件使用示例

## 概述

QmdevHA 组件现在设计为事件实体，它会监听 ZMQ 消息并触发 Home Assistant 事件，而不是直接控制设备。这样设计的好处是：

1. **解耦**: 组件只负责接收和解析 ZMQ 消息，不直接控制设备
2. **灵活性**: Home Assistant 可以通过自动化来处理这些事件，实现更复杂的逻辑
3. **可扩展性**: 用户可以轻松添加新的设备控制逻辑，而不需要修改组件代码

## 触发的事件

### 1. qmdevha_key_event

当接收到按键事件时触发。

**事件数据:**
```json
{
  "qid": 9,
  "key": 19,
  "isrelease": true,
  "timestamp": 1640995200.0
}
```

**字段说明:**
- `qid`: 队列ID
- `key`: 按键代码 (0x13 = 19)
- `isrelease`: 是否为释放事件 (true=释放, false=按下)
- `timestamp`: 事件时间戳

### 2. qmdevha_pack_event

当接收到打包事件时触发。

**事件数据:**
```json
{
  "onoff": true,
  "timestamp": 1640995200.0
}
```

**字段说明:**
- `onoff`: 开关状态 (true=开, false=关)
- `timestamp`: 事件时间戳

## 自动化示例

### 示例1: 按键控制灯光

```yaml
# configuration.yaml
automation:
  - alias: "QmdevHA 按键控制灯光"
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
        entity_id: light.living_room
```

### 示例2: 打包事件控制空调

```yaml
# configuration.yaml
automation:
  - alias: "QmdevHA 打包事件控制空调"
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
                entity_id: climate.living_room_ac
                data:
                  hvac_mode: cool
          - conditions:
              - condition: template
                value_template: "{{ not trigger.event.data.onoff }}"
            sequence:
              - service: climate.set_hvac_mode
                entity_id: climate.living_room_ac
                data:
                  hvac_mode: off
```

### 示例3: 复杂逻辑 - 根据时间控制设备

```yaml
# configuration.yaml
automation:
  - alias: "QmdevHA 智能按键控制"
    trigger:
      - platform: event
        event_type: qmdevha_key_event
        event_data:
          qid: 9
          key: 19
    action:
      - choose:
          - conditions:
              - condition: time
                after: "18:00:00"
                before: "23:00:00"
            sequence:
              - service: light.turn_on
                entity_id: light.living_room
                data:
                  brightness: 255
                  color_name: warm_white
          - conditions:
              - condition: time
                after: "23:00:00"
                before: "06:00:00"
            sequence:
              - service: light.turn_on
                entity_id: light.bedroom_nightlight
                data:
                  brightness: 50
```

### 示例4: 多设备联动

```yaml
# configuration.yaml
automation:
  - alias: "QmdevHA 场景控制"
    trigger:
      - platform: event
        event_type: qmdevha_pack_event
        event_data:
          onoff: true
    action:
      - service: scene.turn_on
        entity_id: scene.movie_mode
      - service: notify.mobile_app_your_phone
        data:
          message: "电影模式已激活"
          title: "QmdevHA 通知"
```

## 调试和监控

### 1. 查看事件日志

在 Home Assistant 的开发者工具中查看事件：

```yaml
# configuration.yaml
logger:
  default: info
  logs:
    custom_components.qmdevha: debug
```

### 2. 事件监听器

创建一个简单的自动化来记录所有 QmdevHA 事件：

```yaml
# configuration.yaml
automation:
  - alias: "记录 QmdevHA 事件"
    trigger:
      - platform: event
        event_type: qmdevha_key_event
      - platform: event
        event_type: qmdevha_pack_event
    action:
      - service: system_log.write
        data:
          message: "QmdevHA 事件: {{ trigger.event.event_type }} - {{ trigger.event.data }}"
          level: info
```

### 3. 状态监控

创建一个传感器来监控最后接收的事件：

```yaml
# configuration.yaml
template:
  - sensor:
      - name: "QmdevHA 最后按键事件"
        state: >
          {% set events = state_attr('sensor.qmdevha_last_key_event', 'events') %}
          {% if events %}
            {{ events[-1].data.key if events[-1].data.key else 'Unknown' }}
          {% else %}
            Unknown
          {% endif %}
        attributes:
          events: >
            {% set events = [] %}
            {% for event in state_attr('sensor.qmdevha_last_key_event', 'events', []) %}
              {% set events = events + [event] %}
            {% endfor %}
            {{ events }}
```

## 最佳实践

1. **事件过滤**: 使用 `event_data` 条件来过滤特定的事件
2. **错误处理**: 在自动化中添加条件检查，确保设备存在且可用
3. **性能优化**: 避免在事件处理中执行耗时操作
4. **日志记录**: 记录重要的事件处理操作，便于调试

## 迁移指南

如果你之前使用的是直接设备控制版本，需要：

1. 移除组件配置中的 `light_entity_id` 和 `ac_entity_id` 参数
2. 移除 `url` 和 `token` 参数（不再需要）
3. 创建自动化来处理 `qmdevha_key_event` 和 `qmdevha_pack_event` 事件
4. 测试新的自动化逻辑

这样的设计让 QmdevHA 组件更加灵活和可扩展，用户可以根据自己的需求自由定制设备控制逻辑。
