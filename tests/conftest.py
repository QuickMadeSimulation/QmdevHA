"""测试配置和共享fixtures"""
import pytest
from unittest.mock import AsyncMock, MagicMock
import asyncio


@pytest.fixture
def event_loop():
    """创建事件循环"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_hass():
    """模拟Home Assistant实例"""
    hass = MagicMock()
    hass.loop = MagicMock()
    hass.loop.time.return_value = 1000.0
    hass.data = {}
    hass.services = MagicMock()
    hass.services.async_call = AsyncMock()
    hass.states = MagicMock()
    hass.states.get = MagicMock()
    return hass


@pytest.fixture
def mock_zmq_context():
    """模拟ZMQ上下文"""
    context = MagicMock()
    context.socket.return_value = MagicMock()
    return context


@pytest.fixture
def mock_zmq_socket():
    """模拟ZMQ套接字"""
    socket = MagicMock()
    socket.connect = MagicMock()
    socket.setsockopt_string = MagicMock()
    socket.close = MagicMock()
    socket.getsockopt.return_value = False
    socket.recv = AsyncMock()
    return socket
