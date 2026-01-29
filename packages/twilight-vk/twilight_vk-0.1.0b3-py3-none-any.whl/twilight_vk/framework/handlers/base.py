from typing import TYPE_CHECKING
from typing import List, Callable
import logging

import asyncio

from ..rules import *
from ...utils.types.response import ResponseHandler
from ..exceptions.handler import (
    ResponseHandlerError
)

if TYPE_CHECKING:
    from ..methods import VkMethods

class BASE_EVENT_HANDLER:

    def __init__(self,
                 vk_methods:'VkMethods',):
        '''
        BASE_EVENT_HANDLER is base handler for vk_api events.
        It contsains the base logic for event handler.
        All child event handlers must inherit it

        :param vk_methods: Initialized VkMethods class which allows to use VK API methods
        :type vk_methods: VkMethods
        '''
        self.logger = logging.getLogger(f"event-handler")
        self.logger.log(1, f"{self.__class__.__name__} event handler is initiated")

        self.vk_methods = vk_methods

        self._funcs: List[dict[list[BaseRule], Callable]] = []
    
    def add(self, 
                func, 
                rules: list):
        '''
        Allows to add callable functions into this handler
        '''
        self._funcs.append(
            {
                "rules": rules,
                "func": func
            }
        )
        self.logger.log(1, f"{func.__name__}() was added to {self.__class__.__name__} "\
                          f"with rules: {[f"{rule.__class__.__name__}" for rule in rules]}")
    
    async def _checkRule(self,
                            rule: BaseRule, 
                            event: dict):
        '''
        Checking rule result for current function and event
        '''
        if not hasattr(rule, "methods") or rule.methods is None:
            await rule._linkVkMethods(self.vk_methods)

        result = await rule._check(event)

        return result

    async def _checkRules(self, func, handler, event):
        '''
        Checks all results
        '''
        self.logger.debug(f"Checking rules for {func.__name__} from {self.__class__.__name__}...")
        rule_results = await asyncio.gather(
            *(self._checkRule(rule, event) for rule in handler["rules"]),
            return_exceptions=False
        )
        self.logger.debug(f"Rules check results: {rule_results}")
        self.logger.debug(f"{func.__name__}'s rules was checked")

        should_stop = False

        for rule in rule_results:
            if isinstance(rule, Exception):
                self.logger.error(f"Got an exception in rules check results. [{rule.__class__.__name__}({rule})]")
                should_stop = True
            if rule is False:
                self.logger.debug(f"One of the rules has returned False")
                should_stop = True

        if should_stop:
            return False
        
        return rule_results
    
    async def _extractArgs(self, rule_results:list):
        '''
        Extracts all args from rule_results after regex rules
        '''
        args = {}
        if isinstance(rule_results, list):
            for result in rule_results:
                if isinstance(result, dict):
                    for key, value in result.items():
                        args.setdefault(key, value)
        return args
   
    async def _handleOutput(self,
                               func,
                               callback: str|ResponseHandler,
                               event):
        '''
        Handles the output from functions which was added to handler

        :param callback: Function's output
        :type callback: str | ResponseHandler
        '''
        self.logger.warning("Output handler is empty. Will be skipped.")
        
    async def _callFunc(self, handler:dict, event:dict):
        '''
        Executes separate function from self.__funcs__ list
        '''
        func = handler["func"]

        rule_results = await self._checkRules(func, handler, event)

        extracted_args = await self._extractArgs(rule_results)
        
        if rule_results is not False:
            self.logger.debug(f"Calling {func.__name__} from {self.__class__.__name__}...")
            if asyncio.iscoroutinefunction(func):
                response = await func(event, **extracted_args)
            else:
                response = func(event, **extracted_args)

            result = await self._handleOutput(func, response, event)
            self.logger.debug(f"{func.__name__} from {self.__class__.__name__} was called")

    async def execute(self, 
                      event: dict, 
                      in_gather: bool = True):
        '''
        Handles the event

        :param in_gather: Flag which switches the handling mode (one after one or all in one)
        :type in_gather: bool
        '''
        self.logger.debug(f"{self.__class__.__name__} is working right now...")
        self.logger.debug(f"Handling mode: {"all in one" if in_gather else "one after one"}")

        if in_gather:
            await asyncio.gather(
                *(self._callFunc(handler, event) for handler in self._funcs),
                return_exceptions=False
            )
        else:
            for handler in self._funcs:
                await self._callFunc(handler, event)

        self.logger.debug(f"{self.__class__.__name__} is finished handling the event")


class MESSAGE_LIKE_HANDLER(BASE_EVENT_HANDLER):
    
    async def _handleOutput(self,
                               func,
                               callback:str|ResponseHandler,
                               event):
        '''
        Handles the output from functions which was added to handler

        :param callback: Function's output
        :type callback: str | ResponseHandler
        '''    
        self.logger.debug(f"Handling response for {self.__class__.__name__}.{func.__name__}...")

        if callback is None:
            self.logger.debug(f"Callback is None. Output handling was skipped")
            return True

        if isinstance(callback, str):
            callback = ResponseHandler(
                peer_ids=event["object"]["message"]["peer_id"],
                message=callback,
                forward={
                    "peer_id": event["object"]["message"]["peer_id"],
                    "conversation_message_ids": event["object"]["message"]["conversation_message_id"],
                    "is_reply": True
                }
            )
        if isinstance(callback, ResponseHandler):
            response = await self.vk_methods.messages.send(**callback.getData())
            return response
        raise ResponseHandlerError(callback, isinstance(callback, ResponseHandler | None))
    


class NOT_MESSAGE_LIKE_HANDLER(BASE_EVENT_HANDLER):

    async def _handleOutput(self,
                               func,
                               callback:str|ResponseHandler,
                               event):
        '''
        Handles the output from functions which was added to handler

        :param callback: Function's output
        :type callback: str | ResponseHandler
        '''    
        self.logger.debug(f"Handling response for {self.__class__.__name__}.{func.__name__}...")

        if callback is None:
            self.logger.debug(f"Callback is None. Output handling was skipped")
            return True
        
        if isinstance(callback, ResponseHandler):
            response = await self.vk_methods.messages.send(**callback.getData())
            return response
        raise ResponseHandlerError(callback, isinstance(callback, ResponseHandler | None))