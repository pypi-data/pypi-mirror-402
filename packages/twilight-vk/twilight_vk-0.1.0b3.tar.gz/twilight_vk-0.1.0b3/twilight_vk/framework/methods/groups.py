from .base import BaseMethodsGroup

class Groups(BaseMethodsGroup):

    async def getById(self,
                      group_ids: list[str] | str = None,
                      group_id: str = None,
                      fields: str = None) -> dict:
        '''
        Возвращает информацию о заданном сообществе или о нескольких сообществах.
        (см. https://dev.vk.com/ru/method/groups.getById)
        '''
        values = {
            "group_ids": ",".join([f"{_group_id}" for _group_id in group_ids]) if isinstance(group_ids, list) else f"{group_ids}",
            "group_id": abs(group_id) if group_id is not None else self.__group_id__,
            "fields": fields,
            "v": self.__api_version__
        }
        response = await self.base_api.base_get_method(api_method=f"{self.method}.getById",
                                                       values=values)
        return response
    
    async def getLongPollServer(self,
                                group_id:int=None) -> dict:
        
        '''
        Возвращает данные для подключения к Bots Longpoll API.
        (см. https://dev.vk.com/ru/method/groups.getLongPollServer)
        '''

        values = {
            "group_id": abs(group_id) if group_id is not None else self.__group_id__,
            "v": self.__api_version__
        }
        response = await self.base_api.base_get_method(api_method=f"{self.method}.getLongPollServer",
                                                       values=values)
        return response
    