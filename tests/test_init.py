"""测试QmdevHA集成初始化"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from custom_components.qmdevha import async_setup_entry, async_unload_entry
from custom_components.qmdevha.const import DOMAIN


@pytest.fixture
def mock_config_entry():
    """模拟配置条目"""
    from tests.common import MockConfigEntry
    return MockConfigEntry(
        domain=DOMAIN,
        title="QmdevHA",
        data={
            "url": "http://localhost:8123",
            "token": "test_token",
            "light_entity_id": "light.test_light",
            "ac_entity_id": "climate.test_ac",
            "zmq_sub_endpoint": "tcp://127.0.0.1:5556",
        },
        unique_id="qmdevha_test",
    )


@pytest.fixture
def mock_hass():
    """模拟Home Assistant实例"""
    hass = MagicMock()
    hass.data = {}
    hass.loop = MagicMock()
    hass.loop.create_task = MagicMock()
    return hass


@pytest.mark.asyncio
async def test_async_setup_entry(mock_hass, mock_config_entry):
    """测试集成设置"""
    mock_task = AsyncMock()
    mock_hass.loop.create_task.return_value = mock_task
    
    with patch('custom_components.qmdevha._run_zmq_bridge_task') as mock_run_task:
        result = await async_setup_entry(mock_hass, mock_config_entry)
        
        assert result is True
        assert DOMAIN in mock_hass.data
        assert mock_config_entry.entry_id in mock_hass.data[DOMAIN]
        mock_hass.loop.create_task.assert_called_once()


@pytest.mark.asyncio
async def test_async_unload_entry(mock_hass, mock_config_entry):
    """测试集成卸载"""
    mock_task = AsyncMock()
    mock_hass.data[DOMAIN] = {mock_config_entry.entry_id: mock_task}
    
    result = await async_unload_entry(mock_hass, mock_config_entry)
    
    assert result is True
    mock_task.cancel.assert_called_once()
    assert mock_config_entry.entry_id not in mock_hass.data[DOMAIN]


@pytest.mark.asyncio
async def test_async_unload_entry_no_task(mock_hass, mock_config_entry):
    """测试卸载不存在的任务"""
    mock_hass.data[DOMAIN] = {}
    
    result = await async_unload_entry(mock_hass, mock_config_entry)
    
    assert result is True


@pytest.mark.asyncio
async def test_run_zmq_bridge_task_cancelled(mock_hass, mock_config_entry):
    """测试ZMQ桥接任务被取消"""
    from custom_components.qmdevha import _run_zmq_bridge_task
    
    with patch('custom_components.qmdevha.ZmqBridge') as mock_bridge_class:
        mock_bridge = AsyncMock()
        mock_bridge.run.side_effect = asyncio.CancelledError()
        mock_bridge_class.return_value = mock_bridge
        
        # 应该不会抛出异常
        await _run_zmq_bridge_task(mock_hass, mock_config_entry)


@pytest.mark.asyncio
async def test_run_zmq_bridge_task_exception(mock_hass, mock_config_entry):
    """测试ZMQ桥接任务异常"""
    from custom_components.qmdevha import _run_zmq_bridge_task
    
    with patch('custom_components.qmdevha.ZmqBridge') as mock_bridge_class:
        mock_bridge = AsyncMock()
        mock_bridge.run.side_effect = Exception("Test error")
        mock_bridge_class.return_value = mock_bridge
        
        # 应该不会抛出异常，但会记录日志
        await _run_zmq_bridge_task(mock_hass, mock_config_entry)
