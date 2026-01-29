from typing import TYPE_CHECKING
import logging
import asyncio

from .event_handlers import *
from ...utils.types.event_types import BotEventType

if TYPE_CHECKING:
    from ..methods import VkMethods
    from ...utils.event_loop import TwiTaskManager

class OnEventLabeler:

    def __init__(self, handlers: dict):
        self.handlers: dict[str, BASE_EVENT_HANDLER] = handlers

    def raw(self, event_type: str, *rules):
        def decorator(func):
            self.handlers[event_type].add(func, rules)
            return func
        return decorator

    def all(self, *rules):
        def decorator(func):
            for handler_name in self.handlers.keys():
                self.handlers[handler_name].add(func, rules)
            return func
        return decorator
    
    def message_new(self, *rules):
        def decorator(func):
            self.handlers[BotEventType.MESSAGE_NEW].add(func, rules)
            return func
        return decorator

class EventRouter:

    def __init__(self,
                 vk_methods:'VkMethods',
                 _loop_wrapper: 'TwiTaskManager'):
        '''
        Router for events.
        Allows to route events to separate event handlers
        '''
        self.vk_methods = vk_methods
        self._loop_wrapper = _loop_wrapper
        self.logger = logging.getLogger("event-router")
        self._handlers = {
            "default": DEFAULT_HANDLER(self.vk_methods),

            # Message events
            BotEventType.MESSAGE_NEW: MESSAGE_NEW(self.vk_methods),
            BotEventType.MESSAGE_REPLY: MESSAGE_REPLY(self.vk_methods),
            BotEventType.MESSAGE_EDIT: MESSAGE_EDIT(self.vk_methods),
            BotEventType.MESSAGE_TYPING_STATE: MESSAGE_TYPING_STATE(self.vk_methods),
            BotEventType.MESSAGE_READ: MESSAGE_READ(self.vk_methods),
            BotEventType.MESSAGE_EVENT: MESSAGE_EVENT(self.vk_methods),
            
            # Photo events
            BotEventType.PHOTO_NEW: PHOTO_NEW(self.vk_methods),
            BotEventType.PHOTO_COMMENT_NEW: PHOTO_COMMENT_NEW(self.vk_methods),
            BotEventType.PHOTO_COMMENT_EDIT: PHOTO_COMMENT_EDIT(self.vk_methods),
            BotEventType.PHOTO_COMMENT_RESTORE: PHOTO_COMMENT_RESTORE(self.vk_methods),
            BotEventType.PHOTO_COMMENT_DELETE: PHOTO_COMMENT_DELETE(self.vk_methods),
            
            # Audio events
            BotEventType.AUDIO_NEW: AUDIO_NEW(self.vk_methods),
            
            # Video events
            BotEventType.VIDEO_NEW: VIDEO_NEW(self.vk_methods),
            BotEventType.VIDEO_COMMENT_NEW: VIDEO_COMMENT_NEW(self.vk_methods),
            BotEventType.VIDEO_COMMENT_EDIT: VIDEO_COMMENT_EDIT(self.vk_methods),
            BotEventType.VIDEO_COMMENT_RESTORE: VIDEO_COMMENT_RESTORE(self.vk_methods),
            BotEventType.VIDEO_COMMENT_DELETE: VIDEO_COMMENT_DELETE(self.vk_methods),
            
            # Wall events
            BotEventType.WALL_POST_NEW: WALL_POST_NEW(self.vk_methods),
            BotEventType.WALL_REPOST: WALL_REPOST(self.vk_methods),
            BotEventType.WALL_SCHEDULE_POST_NEW: WALL_SCHEDULE_POST_NEW(self.vk_methods),
            BotEventType.WALL_SCHEDULE_POST_DELETE: WALL_SCHEDULE_POST_DELETE(self.vk_methods),
            BotEventType.WALL_REPLY_NEW: WALL_REPLY_NEW(self.vk_methods),
            BotEventType.WALL_REPLY_EDIT: WALL_REPLY_EDIT(self.vk_methods),
            BotEventType.WALL_REPLY_RESTORE: WALL_REPLY_RESTORE(self.vk_methods),
            BotEventType.WALL_REPLY_DELETE: WALL_REPLY_DELETE(self.vk_methods),
            
            # Like events
            BotEventType.LIKE_ADD: LIKE_ADD(self.vk_methods),
            BotEventType.LIKE_REMOVE: LIKE_REMOVE(self.vk_methods),
            
            # Board events
            # BotEventType.BOARD_POST_NEW: BOARD_POST_NEW(self.vk_methods),
            # BotEventType.BOARD_POST_EDIT: BOARD_POST_EDIT(self.vk_methods),
            # BotEventType.BOARD_POST_RESTORE: BOARD_POST_RESTORE(self.vk_methods),
            # BotEventType.BOARD_POST_DELETE: BOARD_POST_DELETE(self.vk_methods),
            
            # Market events
            # BotEventType.MARKET_COMMENT_NEW: MARKET_COMMENT_NEW(self.vk_methods),
            # BotEventType.MARKET_COMMENT_EDIT: MARKET_COMMENT_EDIT(self.vk_methods),
            # BotEventType.MARKET_COMMENT_RESTORE: MARKET_COMMENT_RESTORE(self.vk_methods),
            # BotEventType.MARKET_COMMENT_DELETE: MARKET_COMMENT_DELETE(self.vk_methods),
            # BotEventType.MARKET_ORDER_NEW: MARKET_ORDER_NEW(self.vk_methods),
            # BotEventType.MARKET_ORDER_EDIT: MARKET_ORDER_EDIT(self.vk_methods),
            
            # Group events
            BotEventType.GROUP_LEAVE: GROUP_LEAVE(self.vk_methods),
            BotEventType.GROUP_JOIN: GROUP_JOIN(self.vk_methods),
            BotEventType.USER_BLOCK: USER_BLOCK(self.vk_methods),
            BotEventType.USER_UNBLOCK: USER_UNBLOCK(self.vk_methods),
            
            # Other events
            # BotEventType.POLL_VOTE_NEW: POLL_VOTE_NEW(self.vk_methods),
            # BotEventType.GROUP_OFFICERS_EDIT: GROUP_OFFICERS_EDIT(self.vk_methods),
            # BotEventType.GROUP_CHANGE_SETTINGS: GROUP_CHANGE_SETTINGS(self.vk_methods),
            # BotEventType.GROUP_CHANGE_PHOTO: GROUP_CHANGE_PHOTO(self.vk_methods),
            # BotEventType.VKPAY_TRANSACTION: VKPAY_TRANSACTION(self.vk_methods),
        }
        self.on_event = OnEventLabeler(self._handlers)
    
    async def handle(self, polling_response: dict):
        '''
        Handles the event list

        :param polling_response: Response from the polling requests contains "ts" and "updates" keys
        :type polling_response: dict
        '''
        self.logger.debug("Routing the events...")
        events = []
        for event in polling_response["updates"]:
            events.append(
                self._loop_wrapper._loop.create_task(
                    self.route(event)
                )
            )
        try:
            await asyncio.gather(*events, return_exceptions=False)
        except Exception as exc:
            self.logger.error(f"{exc.__class__.__name__}: {exc}", exc_info=True)

    async def route(self, current_event: dict):
        '''
        Routing the event to the exact handler
        '''
        event_type = current_event.get("type", "default")
        handler: BASE_EVENT_HANDLER = self._handlers.get(event_type, self._handlers["default"])
        self.logger.debug(f"Routing the event {current_event.get("type")} to the {handler.__class__.__name__} handler")
        await handler.execute(current_event)