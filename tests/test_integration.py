"""集成测试 - 测试完整的QmdevHA集成"""
import pytest
import asyncio
import struct
from unittest.mock import AsyncMock, MagicMock, patch
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from custom_components.qmdevha.const import DOMAIN


@pytest.fixture
def integration_config():
    """集成测试配置"""
    return {
        "url": "http://localhost:8123",
        "token": "test_token",
        "light_entity_id": "light.test_light",
        "ac_entity_id": "climate.test_ac",
        "zmq_sub_endpoint": "tcp://127.0.0.1:5556",
    }


@pytest.fixture
async def setup_integration(hass: HomeAssistant, integration_config):
    """设置集成用于测试"""
    from tests.common import MockConfigEntry
    
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        title="QmdevHA",
        data=integration_config,
        unique_id="qmdevha_integration_test",
    )
    config_entry.add_to_hass(hass)
    
    with patch('zmq.asyncio.Context') as mock_context, \
         patch('aiohttp.ClientSession') as mock_session:
        
        # 模拟ZMQ上下文和套接字
        mock_ctx = MagicMock()
        mock_sock = MagicMock()
        mock_ctx.socket.return_value = mock_sock
        mock_context.return_value = mock_ctx
        
        # 模拟HTTP会话
        mock_http_session = AsyncMock()
        mock_session.return_value = mock_http_session
        
        await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()
        
        return config_entry, mock_ctx, mock_sock, mock_http_session


@pytest.mark.asyncio
async def test_integration_setup_and_teardown(hass: HomeAssistant, setup_integration):
    """测试集成的设置和拆卸"""
    config_entry, mock_ctx, mock_sock, mock_http_session = await setup_integration
    
    # 验证集成已设置
    assert DOMAIN in hass.data
    assert config_entry.entry_id in hass.data[DOMAIN]
    
    # 验证ZMQ套接字已连接
    mock_sock.connect.assert_called_once_with("tcp://127.0.0.1:5556")
    mock_sock.setsockopt_string.assert_called_once_with("", "")
    
    # 测试卸载
    await hass.config_entries.async_unload(config_entry.entry_id)
    await hass.async_block_till_done()
    
    # 验证任务已取消
    assert config_entry.entry_id not in hass.data[DOMAIN]


@pytest.mark.asyncio
async def test_zmq_message_processing(hass: HomeAssistant, setup_integration):
    """测试ZMQ消息处理"""
    config_entry, mock_ctx, mock_sock, mock_http_session = await setup_integration
    
    # 模拟心跳消息
    heartbeat_msg = struct.pack("<ii", 0x07324D6D, 0)  # ZMQQHeartBeat_ID
    mock_sock.recv.return_value = heartbeat_msg
    
    # 模拟按键事件消息 - 开灯
    key_event_msg = struct.pack("<ii", 0x07324D6E, 12) + struct.pack("<iii", 9, 0x13, 1)
    mock_sock.recv.return_value = key_event_msg
    
    # 模拟打包事件消息 - 开空调
    pack_event_msg = struct.pack("<ii", 0x07324D6F, 1) + struct.pack("?", True)
    mock_sock.recv.return_value = pack_event_msg
    
    # 由于实际的ZMQ桥接器在后台运行，我们主要测试消息格式的正确性
    # 这里可以添加更多的消息处理测试


@pytest.mark.asyncio
async def test_ha_api_calls(hass: HomeAssistant, setup_integration):
    """测试Home Assistant API调用"""
    config_entry, mock_ctx, mock_sock, mock_http_session = await setup_integration
    
    # 模拟HTTP响应
    mock_resp = AsyncMock()
    mock_resp.status = 200
    mock_resp.text = AsyncMock(return_value="OK")
    mock_http_session.post.return_value.__aenter__.return_value = mock_resp
    
    # 测试灯光控制API调用
    from custom_components.qmdevha.bridge import ZmqBridge
    
    bridge = ZmqBridge(
        ha_base_url="http://localhost:8123",
        ha_token="test_token",
        light_entity_id="light.test_light",
        ac_entity_id="climate.test_ac",
        zmq_sub_endpoint="tcp://127.0.0.1:5556",
    )
    
    # 测试开灯
    await bridge._turn_on_light()
    mock_http_session.post.assert_called_with(
        "http://localhost:8123/api/services/switch/turn_on",
        json={"entity_id": "light.test_light"},
        timeout=10
    )
    
    # 测试关灯
    await bridge._turn_off_light()
    
    # 测试开空调
    await bridge._turn_on_ac()
    
    # 测试关空调
    await bridge._turn_off_ac()


@pytest.mark.asyncio
async def test_error_handling(hass: HomeAssistant, setup_integration):
    """测试错误处理"""
    config_entry, mock_ctx, mock_sock, mock_http_session = await setup_integration
    
    # 测试HTTP错误
    mock_resp = AsyncMock()
    mock_resp.status = 400
    mock_resp.text = AsyncMock(return_value="Bad Request")
    mock_http_session.post.return_value.__aenter__.return_value = mock_resp
    
    from custom_components.qmdevha.bridge import ZmqBridge
    
    bridge = ZmqBridge(
        ha_base_url="http://localhost:8123",
        ha_token="test_token",
        light_entity_id="light.test_light",
        ac_entity_id="climate.test_ac",
        zmq_sub_endpoint="tcp://127.0.0.1:5556",
    )
    
    # 应该抛出RuntimeError
    with pytest.raises(RuntimeError, match="Bad Request"):
        await bridge._turn_on_light()


@pytest.mark.asyncio
async def test_invalid_message_handling(hass: HomeAssistant, setup_integration):
    """测试无效消息处理"""
    config_entry, mock_ctx, mock_sock, mock_http_session = await setup_integration
    
    from custom_components.qmdevha.bridge import ZmqBridge
    
    bridge = ZmqBridge(
        ha_base_url="http://localhost:8123",
        ha_token="test_token",
        light_entity_id="light.test_light",
        ac_entity_id="climate.test_ac",
        zmq_sub_endpoint="tcp://127.0.0.1:5556",
    )
    
    # 测试无效的按键事件数据
    invalid_payload = b"invalid_data"
    await bridge._handle_key_event(invalid_payload)  # 应该不会抛出异常
    
    # 测试无效的打包事件数据
    await bridge._handle_pack_event(b"")  # 应该不会抛出异常
