import httpx


class Slack:
    def __init__(self, webHook: str):
        self.__webHook = webHook

    def _format_message(self, message: str, box_message: str | None = None) -> str:
        '''메시지 포맷팅 헬퍼 함수'''
        return f'{message}\n```{box_message}```' if box_message else message

    async def async_send_message(self, message: str, box_message: str | None = None) -> bool:
        async with httpx.AsyncClient() as client:
            res = await client.post(self.__webHook, json={'text': self._format_message(message, box_message)})
            return res.status_code == httpx.codes.OK

    def send_message(self, message: str, box_message: str | None = None) -> bool:
        res = httpx.post(self.__webHook, json={'text': self._format_message(message, box_message)})
        return res.status_code == httpx.codes.OK
