from Server.API import *

class BaseRequest:
    def __init__(self, api = API_CANT_DECODE_ANY_MSG):
        self.api_code = api

    def __str__(self):
        return "API: " + self.api_code

