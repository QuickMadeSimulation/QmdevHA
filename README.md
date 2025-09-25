# QmdevHA（HACS 自定义集成）

一个 Home Assistant 自定义集成：通过 ZMQ 订阅按键/打包事件，联动控制 Home Assistant 中的灯光与空调等设备。现已支持通过 HACS 安装。

## 概述

QmdevHA 将奎克质造（QuickmadeSim）设备发出的 ZMQ 消息桥接到 Home Assistant。通过 config flow 在前端配置 `HA URL/Token`、`灯光实体`、`空调实体` 和 `ZMQ 订阅端点`，后台守护协程会持续监听并调用 HA 服务。

### 支持的设备
- **按键消息来源**：
  - qmdev 7.1 及以上版本
  - qmdevsimconnect 5.1 及以上版本

## 功能特性

- 🔌 **ZMQ 消息订阅**：实时监听按键事件消息队列
- 🏠 **智能设备控制**：支持灯光和空调设备的自动控制
- 🎯 **精确按键映射**：支持多个按键事件（灯光控制、空调控制）
- 🛡️ **错误处理**：完善的异常处理和日志记录
- 🔄 **优雅退出**：支持信号处理和资源清理
- ⚙️ **灵活配置**：通过环境变量进行配置管理

## 通过 HACS 安装

1. 在 Home Assistant 前端 → HACS → 集成 → 右上角菜单 → 自定义存储库，添加仓库：`https://github.com/cpuwolf/QmdevHA`，类别选择 `集成`。
2. 在 HACS 搜索 `QmdevHA` 并安装。
3. 安装完成后，前往 设置 → 设备与服务 → 添加集成 → 搜索 `QmdevHA`，根据向导填写：
   - `HA URL`（例如 `http://homeassistant.local:8123`）
   - `HA Token`（长效访问令牌）
   - `灯光实体 ID`（如 `light.living_room`）
   - `空调实体 ID`（如 `climate.living_room_ac`）
   - `ZMQ 订阅端点`（如 `tcp://127.0.0.1:5556`）

## 工作原理

1. **ZMQ 订阅**：程序作为 ZMQ SUB 客户端连接到指定的端点
2. **消息解析**：接收并解析特定格式的按键事件消息
3. **灯光/空调控制**：根据按键状态调用 Home Assistant REST API
   - 按键释放时：打开灯光
   - 按键按下时：关闭灯光

## 兼容性与依赖

- Home Assistant：2024.6.0+
- 依赖：`pyzmq`、`aiohttp`、`voluptuous`

## 开发者说明

- 自定义集成代码位于 `custom_components/QmdevHA/`
- 旧的独立脚本仍在 `src/` 中，已不再用于 HA 集成
- **消息 ID**：`0x07324D6E`（ZMQQ_KEYEVENT_ID）
- **负载结构**：`qid`（4字节）+ `key`（4字节）+ `isrelease`（4字节）
- **字节序**：小端序（little-endian）

## 按键映射

程序支持以下按键事件映射：

| 设备 ID | 按键码 | 功能 | 设备类型 | 操作 |
|---------|--------|------|----------|------|
| `9` | `0x13` | DOME LT | 灯光 | 按键释放→开灯，按键按下→关灯 |
| `9` | `0x22` | PACK 1 | 空调 | 按键释放→制冷模式，按键按下→关闭空调 |

### 按键状态说明
- `isrelease = 1`：按键释放（松开）
- `isrelease = 0`：按键按下

## 配置说明

| 参数 | 说明 | 示例 | 必需 |
|------|------|------|------|
| `HA_BASE_URL` | Home Assistant 服务器地址 | `http://127.0.0.1:8123` | ✅ |
| `HA_TOKEN` | HA 长效访问令牌 | 从 HA 前端获取 | ✅ |
| `HA_LIGHT_ENTITY_ID` | 灯光设备实体 ID | `light.bedroom` | ✅ |
| `HA_AC_ENTITY_ID` | 空调设备实体 ID | `climate.living_room_ac` | ✅ |
| `ZMQ_SUB_ENDPOINT` | ZMQ 订阅端点 | `tcp://127.0.0.1:5556` | ✅ |

## 技术栈

- **Python 3.10+**
- **PyZMQ**：ZeroMQ Python 绑定
- **Requests**：HTTP 客户端
- **python-dotenv**：环境变量管理


## 故障排除

### 常见问题

**1. 程序无法连接到 ZMQ**
```
检查 ZMQ_SUB_ENDPOINT 配置是否正确
确认 qmdev 或 qmdevsimconnect 服务正在运行
```

**2. Home Assistant 设备控制失败**
```
检查 HA_BASE_URL 和 HA_TOKEN 是否正确
确认设备实体 ID 在 HA 中存在
查看程序日志获取详细错误信息
```

**3. 按键事件未被处理**
```
确认按键映射表中的设备 ID 和按键码
检查 ZMQ 消息格式是否符合预期
```

## 退出程序

使用 `Ctrl+C` 优雅退出，程序会自动清理 ZMQ 资源。


