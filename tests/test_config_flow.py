"""测试QmdevHA配置流程"""
import pytest
from unittest.mock import patch, AsyncMock
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.qmdevha.const import DOMAIN
from custom_components.qmdevha.config_flow import QmdevHAConfigFlow


@pytest.fixture
def mock_config_entry():
    """模拟配置条目"""
    from tests.common import MockConfigEntry
    return MockConfigEntry(
        domain=DOMAIN,
        title="QmdevHA",
        data={
            "zmq_sub_endpoint": "tcp://127.0.0.1:5556",
        },
        unique_id="qmdevha_test",
    )


async def test_config_flow_form(hass: HomeAssistant) -> None:
    """测试配置流程表单"""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == FlowResultType.FORM
    assert result["errors"] is None


async def test_config_flow_success(hass: HomeAssistant) -> None:
    """测试配置流程成功"""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "zmq_sub_endpoint": "tcp://127.0.0.1:5556",
        },
    )
    
    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["title"] == "QmdevHA"
    assert result["data"] == {
        "zmq_sub_endpoint": "tcp://127.0.0.1:5556",
    }


async def test_config_flow_validation_error(hass: HomeAssistant) -> None:
    """测试配置流程验证错误"""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    
    # 测试空值验证
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "zmq_sub_endpoint": "",
        },
    )
    
    # 应该显示表单错误
    assert result["type"] == FlowResultType.FORM
