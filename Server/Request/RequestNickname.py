from Server.API import *
from Server.Request.BaseRequest import BaseRequest

class RequestNickname (BaseRequest):

    def __init__(self):
        super().__init__(API_SEND_NAME)

    def setData(self, nickname):
        self.nickname = nickname

    def __str__(self):
        return "API: " + self.api_code + ", Nickname: " + self.nickname