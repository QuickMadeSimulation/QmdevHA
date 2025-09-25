"""测试ZMQ桥接功能"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import struct

from custom_components.qmdevha.bridge import ZmqBridge


@pytest.fixture
def mock_bridge():
    """创建模拟的ZMQ桥接器"""
    return ZmqBridge(
        ha_base_url="http://localhost:8123",
        ha_token="test_token",
        light_entity_id="light.test_light",
        ac_entity_id="climate.test_ac",
        zmq_sub_endpoint="tcp://127.0.0.1:5556",
    )


@pytest.fixture
def mock_hass():
    """模拟Home Assistant实例"""
    hass = MagicMock()
    hass.loop = asyncio.get_event_loop()
    hass.loop.time.return_value = 1000.0
    return hass


@pytest.mark.asyncio
async def test_turn_on_light(mock_bridge):
    """测试开灯功能"""
    with patch.object(mock_bridge, '_post') as mock_post:
        await mock_bridge._turn_on_light()
        mock_post.assert_called_once_with(
            "/api/services/switch/turn_on",
            {"entity_id": "light.test_light"}
        )


@pytest.mark.asyncio
async def test_turn_off_light(mock_bridge):
    """测试关灯功能"""
    with patch.object(mock_bridge, '_post') as mock_post:
        await mock_bridge._turn_off_light()
        mock_post.assert_called_once_with(
            "/api/services/switch/turn_off",
            {"entity_id": "light.test_light"}
        )


@pytest.mark.asyncio
async def test_turn_on_ac(mock_bridge):
    """测试开空调功能"""
    with patch.object(mock_bridge, '_post') as mock_post:
        await mock_bridge._turn_on_ac()
        mock_post.assert_called_once_with(
            "/api/services/climate/set_hvac_mode",
            {"entity_id": "climate.test_ac", "hvac_mode": "cool"}
        )


@pytest.mark.asyncio
async def test_turn_off_ac(mock_bridge):
    """测试关空调功能"""
    with patch.object(mock_bridge, '_post') as mock_post:
        await mock_bridge._turn_off_ac()
        mock_post.assert_called_once_with(
            "/api/services/climate/set_hvac_mode",
            {"entity_id": "climate.test_ac", "hvac_mode": "off"}
        )


@pytest.mark.asyncio
async def test_handle_key_event_light_on(mock_bridge):
    """测试按键事件处理 - 开灯"""
    # 构造按键事件数据：qid=9, key=0x13, isrelease=1
    payload = struct.pack("<iii", 9, 0x13, 1)
    
    with patch.object(mock_bridge, '_turn_on_light') as mock_turn_on:
        await mock_bridge._handle_key_event(payload)
        mock_turn_on.assert_called_once()


@pytest.mark.asyncio
async def test_handle_key_event_light_off(mock_bridge):
    """测试按键事件处理 - 关灯"""
    # 构造按键事件数据：qid=9, key=0x13, isrelease=0
    payload = struct.pack("<iii", 9, 0x13, 0)
    
    with patch.object(mock_bridge, '_turn_off_light') as mock_turn_off:
        await mock_bridge._handle_key_event(payload)
        mock_turn_off.assert_called_once()


@pytest.mark.asyncio
async def test_handle_pack_event_ac_on(mock_bridge):
    """测试打包事件处理 - 开空调"""
    # 构造打包事件数据：onoff=True
    payload = struct.pack("?", True)
    
    with patch.object(mock_bridge, '_turn_on_ac') as mock_turn_on:
        await mock_bridge._handle_pack_event(payload)
        mock_turn_on.assert_called_once()


@pytest.mark.asyncio
async def test_handle_pack_event_ac_off(mock_bridge):
    """测试打包事件处理 - 关空调"""
    # 构造打包事件数据：onoff=False
    payload = struct.pack("?", False)
    
    with patch.object(mock_bridge, '_turn_off_ac') as mock_turn_off:
        await mock_bridge._handle_pack_event(payload)
        mock_turn_off.assert_called_once()


@pytest.mark.asyncio
async def test_handle_invalid_key_event(mock_bridge):
    """测试无效按键事件处理"""
    # 构造无效的按键事件数据（长度不足）
    payload = b"invalid"
    
    with patch.object(mock_bridge, '_turn_on_light') as mock_turn_on:
        await mock_bridge._handle_key_event(payload)
        mock_turn_on.assert_not_called()


@pytest.mark.asyncio
async def test_handle_invalid_pack_event(mock_bridge):
    """测试无效打包事件处理"""
    # 构造无效的打包事件数据（空数据）
    payload = b""
    
    with patch.object(mock_bridge, '_turn_on_ac') as mock_turn_on:
        await mock_bridge._handle_pack_event(payload)
        mock_turn_on.assert_not_called()


@pytest.mark.asyncio
async def test_ensure_session(mock_bridge):
    """测试HTTP会话创建"""
    session = await mock_bridge._ensure_session()
    assert session is not None
    assert session.headers["Authorization"] == "Bearer test_token"
    assert session.headers["Content-Type"] == "application/json"


@pytest.mark.asyncio
async def test_post_request_success(mock_bridge):
    """测试POST请求成功"""
    with patch('aiohttp.ClientSession.post') as mock_post:
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.text = AsyncMock(return_value="OK")
        mock_post.return_value.__aenter__.return_value = mock_resp
        
        await mock_bridge._post("/api/test", {"test": "data"})
        mock_post.assert_called_once()


@pytest.mark.asyncio
async def test_post_request_error(mock_bridge):
    """测试POST请求错误"""
    with patch('aiohttp.ClientSession.post') as mock_post:
        mock_resp = AsyncMock()
        mock_resp.status = 400
        mock_resp.text = AsyncMock(return_value="Bad Request")
        mock_post.return_value.__aenter__.return_value = mock_resp
        
        with pytest.raises(RuntimeError, match="Bad Request"):
            await mock_bridge._post("/api/test", {"test": "data"})
