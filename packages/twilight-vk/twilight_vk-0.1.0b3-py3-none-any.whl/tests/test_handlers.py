import pytest
import asyncio

from twilight_vk import TwilightVK
from twilight_vk.framework.rules import TrueRule
from twilight_vk.framework.exceptions.framework import FrameworkError
from twilight_vk.utils.types.event_types import BotEventType

@pytest.fixture
def bot():
    botInst = TwilightVK(
        ACCESS_TOKEN="123",
        GROUP_ID=123
    )
    return botInst

class MockPolling:

    def get() -> dict:
        events = {"updates": []}
        for attr_name, attr_value in vars(BotEventType).items():
            if "__" not in attr_name:
                events["updates"].append({"type": attr_value, "object": {"message": {"peer_id": 123, "conversation_message_id": 1}}})
        return events

    
@pytest.mark.asyncio
async def test_labeler(bot: TwilightVK, caplog):

    @bot.on_event.all(TrueRule())
    async def handle(event: dict):
        return "OK"
    
    for record in caplog.records:
        if record.levelname == "INIT":
            assert record.message in ["Rule TrueRule() is initiated",
                                      "handle() was added to MESSAGE_NEW with rules: ['TrueRule']",
                                      "handle() was added to MESSAGE_REPLY with rules: ['TrueRule']",
                                      "handle() was added to DEFAULT_HANDLER with rules: ['TrueRule']"]
    for handler_name in bot.__bot__._router._handlers.keys():
        assert bot.__bot__._router._handlers[handler_name]._funcs[0].get("func", False) == handle
        assert isinstance(bot.__bot__._router._handlers[handler_name]._funcs[0].get("rules")[0], TrueRule)
    
@pytest.mark.asyncio
async def test_eventhandlers(monkeypatch):

    _bot = TwilightVK(ACCESS_TOKEN="123", GROUP_ID=123)
    
    @_bot.on_event.all(TrueRule())
    async def handle(event: dict):
        assert isinstance(event, dict)
        assert event.keys() == {'type': 'test', 'object': 'test'}.keys()
        return "OK"
    
    @_bot.on_event.all(TrueRule())
    async def handle2(event: dict):
        assert isinstance(event, dict)
        assert event.keys() == {'type': 'test', 'object': 'test'}.keys()
    
    async def fake_messageSend(*args, **kwargs):
        return True
    
    for handler_name in _bot.__bot__._router._handlers.keys():
        monkeypatch.setattr(_bot.__bot__._router._handlers[handler_name].vk_methods.messages, "send", fake_messageSend)

    results = await asyncio.gather(
        *(_bot.__bot__._router.route(event) for event in MockPolling.get()["updates"]),
        return_exceptions=False
    )
    for result in results:
        
        if result is None:
            assert True
            continue

        assert result