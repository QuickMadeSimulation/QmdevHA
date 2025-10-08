"""测试ZMQ桥接功能（独立于 Home Assistant 环境）"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import struct

# 使该文件在 `-m github` 过滤时被选择
pytestmark = pytest.mark.github

from custom_components.qmdevha.bridge import ZmqBridge


@pytest.fixture
def mock_bridge(mock_hass):
    """创建模拟的ZMQ桥接器"""
    return ZmqBridge(
        hass=mock_hass,
        zmq_sub_endpoint="192.168.1.100",
    )


@pytest.fixture
def mock_hass():
    """模拟 Home Assistant 实例（最小接口）"""
    hass = MagicMock()
    hass.loop = MagicMock()
    hass.loop.time.return_value = 1000.0
    hass.bus = MagicMock()
    hass.bus.async_fire = AsyncMock()
    return hass


@pytest.mark.asyncio
async def test_handle_key_event(mock_bridge):
    """测试按键事件处理 - 触发事件"""
    # 构造按键事件数据：qid=9, key=0x13, isrelease=1
    payload = struct.pack("<iii", 9, 0x13, 1)
    
    await mock_bridge._handle_key_event(payload)
    
    # 验证事件被触发
    mock_bridge._hass.bus.async_fire.assert_called_once_with(
        "qmdevha_key_event",
        {
            "qid": 9,
            "key": 0x13,
            "isrelease": True,
            "timestamp": 1000.0
        }
    )


@pytest.mark.asyncio
async def test_handle_pack_event(mock_bridge):
    """测试打包事件处理 - 触发事件"""
    # 构造打包事件数据：onoff=1, degree=26
    payload = struct.pack("<ii", 1, 26)
    
    await mock_bridge._handle_pack_event(payload)
    
    # 验证事件被触发
    mock_bridge._hass.bus.async_fire.assert_called_once_with(
        "qmdevha_pack_event",
        {
            "onoff": True,
            "degree": 26,
            "timestamp": 1000.0
        }
    )


@pytest.mark.asyncio
async def test_handle_invalid_key_event(mock_bridge):
    """测试无效按键事件处理"""
    # 构造无效的按键事件数据（长度不足）
    payload = b"invalid"
    
    await mock_bridge._handle_key_event(payload)
    
    # 验证没有事件被触发
    mock_bridge._hass.bus.async_fire.assert_not_called()


@pytest.mark.asyncio
async def test_handle_invalid_pack_event(mock_bridge):
    """测试无效打包事件处理"""
    # 构造无效的打包事件数据（长度不足）
    payload = b""
    
    await mock_bridge._handle_pack_event(payload)
    
    # 验证没有事件被触发
    mock_bridge._hass.bus.async_fire.assert_not_called()
