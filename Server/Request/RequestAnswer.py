from Server.API import *
from Server.Request.BaseRequest import BaseRequest

class RequestAnswer(BaseRequest):

    def __init__(self):
        super().__init__(API_SEND_ANSWER)

    def setData (self, guess, keyword):
        self.guess = guess
        self.keyword = keyword

    def __str__(self):
        return "API: " + self.api_code + ", guess: " + self.guess + ", Keyword: " + self.keyword

