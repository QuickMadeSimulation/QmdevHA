# QmdevHA 测试指南

本指南详细说明如何在Home Assistant中测试QmdevHA自定义集成。

## 目录

1. [测试环境设置](#测试环境设置)
2. [运行测试](#运行测试)
3. [测试类型说明](#测试类型说明)
4. [手动测试步骤](#手动测试步骤)
5. [调试和故障排除](#调试和故障排除)

## 测试环境设置

### 1. 安装测试依赖

```bash
# 安装Python测试依赖
pip install -r requirements_test.txt

# 或者手动安装
pip install pytest pytest-asyncio pytest-cov pytest-mock aioresponses
```

### 2. 设置Home Assistant开发环境

```bash
# 克隆Home Assistant核心仓库（用于测试工具）
git clone https://github.com/home-assistant/core.git
cd core

# 安装Home Assistant开发依赖
pip install -r requirements_test.txt
pip install -r requirements_test_all.txt
```

### 3. 准备测试环境

确保您的系统已安装：
- Python 3.10+
- ZMQ库 (`pip install pyzmq`)
- aiohttp (`pip install aiohttp`)

## 运行测试

### 快速测试

```bash
# 运行所有测试
python run_tests.py

# 或者直接使用pytest
pytest tests/ -v
```

### 分类测试

```bash
# 只运行单元测试
pytest tests/test_bridge.py tests/test_config_flow.py tests/test_init.py -v

# 只运行集成测试
pytest tests/test_integration.py -v

# 运行特定测试文件
pytest tests/test_bridge.py -v

# 运行特定测试函数
pytest tests/test_bridge.py::test_turn_on_light -v
```

### 带覆盖率的测试

```bash
# 生成覆盖率报告
pytest tests/ --cov=custom_components.qmdevha --cov-report=term-missing --cov-report=html

# 查看HTML覆盖率报告
open htmlcov/index.html
```

## 测试类型说明

### 1. 单元测试 (`test_bridge.py`)

测试ZMQ桥接器的核心功能：

- **灯光控制**: 测试开灯/关灯功能
- **空调控制**: 测试空调开关和模式设置
- **消息处理**: 测试ZMQ消息解析和处理
- **错误处理**: 测试异常情况的处理
- **HTTP请求**: 测试与Home Assistant的API通信

### 2. 配置流程测试 (`test_config_flow.py`)

测试用户配置界面：

- **表单验证**: 测试配置表单的验证逻辑
- **配置保存**: 测试配置数据的保存
- **错误处理**: 测试配置错误的情况

### 3. 初始化测试 (`test_init.py`)

测试集成的生命周期：

- **集成设置**: 测试集成启动过程
- **任务管理**: 测试后台任务的创建和管理
- **集成卸载**: 测试集成卸载和资源清理

### 4. 集成测试 (`test_integration.py`)

测试完整的集成流程：

- **端到端测试**: 测试从ZMQ消息到HA设备控制的完整流程
- **消息处理**: 测试各种ZMQ消息类型的处理
- **API调用**: 测试与Home Assistant的完整交互

## 手动测试步骤

### 1. 在Home Assistant中安装集成

1. 将`custom_components/qmdevha`目录复制到您的HA配置目录
2. 重启Home Assistant
3. 前往 **设置** → **设备与服务** → **添加集成**
4. 搜索 `QmdevHA` 并添加

### 2. 配置集成

填写以下配置项：

- **HA URL**: `http://homeassistant.local:8123`
- **HA Token**: 您的长效访问令牌
- **灯光实体 ID**: `light.living_room`（或您现有的灯光实体）
- **空调实体 ID**: `climate.living_room_ac`（或您现有的空调实体）
- **ZMQ 订阅端点**: `tcp://127.0.0.1:5556`

### 3. 测试ZMQ消息

#### 模拟按键事件

```python
import zmq
import struct

# 连接到ZMQ发布端
context = zmq.Context()
socket = context.socket(zmq.PUB)
socket.bind("tcp://127.0.0.1:5556")

# 发送按键事件 - 开灯
msg_id = 0x07324D6E  # ZMQQ_KEYEVENT_ID
payload = struct.pack("<iii", 9, 0x13, 1)  # qid=9, key=0x13, isrelease=1
message = struct.pack("<ii", msg_id, len(payload)) + payload
socket.send(message)

# 发送按键事件 - 关灯
payload = struct.pack("<iii", 9, 0x13, 0)  # qid=9, key=0x13, isrelease=0
message = struct.pack("<ii", msg_id, len(payload)) + payload
socket.send(message)

socket.close()
context.term()
```

#### 模拟打包事件

```python
import zmq
import struct

# 连接到ZMQ发布端
context = zmq.Context()
socket = context.socket(zmq.PUB)
socket.bind("tcp://127.0.0.1:5556")

# 发送打包事件 - 开空调
msg_id = 0x07324D6F  # ZMQQ_PACKEVENT_ID
payload = struct.pack("?", True)  # onoff=True
message = struct.pack("<ii", msg_id, len(payload)) + payload
socket.send(message)

# 发送打包事件 - 关空调
payload = struct.pack("?", False)  # onoff=False
message = struct.pack("<ii", msg_id, len(payload)) + payload
socket.send(message)

socket.close()
context.term()
```

### 4. 验证设备控制

1. 发送ZMQ消息后，检查Home Assistant中的设备状态
2. 确认灯光和空调按预期响应
3. 查看Home Assistant日志中的集成日志

## 调试和故障排除

### 1. 启用调试日志

在Home Assistant的`configuration.yaml`中添加：

```yaml
logger:
  default: info
  logs:
    custom_components.qmdevha: debug
```

### 2. 检查日志

查看Home Assistant日志中的QmdevHA相关消息：

```bash
# 在HA容器中查看日志
docker logs homeassistant | grep QmdevHA

# 或者在HA前端查看
开发者工具 → 日志
```

### 3. 常见问题

#### ZMQ连接失败
- 检查ZMQ端点配置是否正确
- 确认ZMQ服务正在运行
- 检查防火墙设置

#### Home Assistant API调用失败
- 验证HA URL和Token是否正确
- 检查实体ID是否存在
- 确认HA服务权限

#### 消息未被处理
- 检查消息格式是否正确
- 验证消息ID是否匹配
- 查看集成日志中的错误信息

### 4. 性能测试

```bash
# 运行性能测试
pytest tests/ --durations=10 -v

# 测试大量消息处理
python -c "
import zmq
import struct
import time

context = zmq.Context()
socket = context.socket(zmq.PUB)
socket.bind('tcp://127.0.0.1:5556')

for i in range(1000):
    msg_id = 0x07324D6E
    payload = struct.pack('<iii', 9, 0x13, i % 2)
    message = struct.pack('<ii', msg_id, len(payload)) + payload
    socket.send(message)
    time.sleep(0.01)

socket.close()
context.term()
"
```

## 持续集成

### GitHub Actions配置

创建`.github/workflows/test.yml`：

```yaml
name: Tests

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.10, 3.11, 3.12]

    steps:
    - uses: actions/checkout@v3
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v3
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements_test.txt
    
    - name: Run tests
      run: |
        pytest tests/ --cov=custom_components.qmdevha --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
```

## 测试最佳实践

1. **测试隔离**: 每个测试应该独立运行，不依赖其他测试
2. **模拟外部依赖**: 使用mock模拟ZMQ和HTTP请求
3. **测试边界条件**: 测试正常情况、异常情况和边界情况
4. **保持测试简单**: 每个测试只验证一个功能点
5. **使用描述性名称**: 测试函数名应该清楚说明测试内容
6. **定期运行测试**: 在开发过程中经常运行测试
7. **维护测试数据**: 使用fixture管理测试数据

## 总结

通过这套完整的测试体系，您可以：

- 验证QmdevHA集成的功能正确性
- 确保代码质量和稳定性
- 快速发现和修复问题
- 支持持续集成和部署

建议在每次代码修改后运行测试，确保集成始终处于良好状态。
