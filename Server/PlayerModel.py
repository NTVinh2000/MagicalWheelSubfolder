import queue

class PlayerModel:

    def __init__(self, socket, clientAddress, id):
        self.id = id
        self.socket = socket    
        self.clientAddress = clientAddress
        self.msgSent = queue.Queue()

        self.nickname = ""
        self.point = 0
        self.disqualified = False

        self.isDisconnected = False

    def __repr__(self):
        return repr((self.nickname, self.point))

    def addPoint(self, pt):
        self.point += pt


    def setNickname(self, nickname):
        self.nickname = nickname

