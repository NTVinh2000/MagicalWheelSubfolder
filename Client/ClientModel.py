import enum
import socket
import time
import sys
from Client.decodeCode import  decodeCode
from Client.Constants import *

class ClientModel:
    class API(enum.Enum):
        SEND_NAME = '0'
        SEND_ANSWER = '3'
        SEND_QUIT = '7'

    numberOfPlayers = 0
    id = -1
    nickname = "Default"
    point = 0
    clientAddress = -1
    serverAddress = '-1'
    serverPort = -1
    isWin = False
    keywordLength = 0
    description = 'One of the most popular interpreter programming languages.'
    timeOut = 0  # to display time left on screen
    dashboard = []  # to display player name, rank, point Ex: {'abc',(1,15)}: 'abc' rank 1 point 15
    keyword = '*y**o*'
    soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    gameTurn = 1
    total = 0
    guessLetter = ''
    guessWord = ''
    rank = 10
    currentPlayingPlayerID = ''

    def __init__(self, serverAddress, serverPort):
        self.serverAddress = serverAddress
        self.serverPort = serverPort

    def displayDashboard(self):
        print(self.dashboard)
        pass

    # use to encode tuple into api msg such as: (0,nickname)-> 0|nickname , (3,letter,keyword)-> 3|letter|keywords4
    def encodeMsg(self, tokens):
        temp = tokens[0]
        if (temp == '0' and len(tokens) == 2) or \
            (temp == '3' and len(tokens) == 3) or \
            (temp == '7' and len(tokens) == 1):
            for token in tokens[1:]:
                temp += '|' + token
            return temp
        else:
            return ''

    def decodeMsg(self, msg):
        tokens = msg.split('|')
        api_code = tokens[0]
        if (BLANK_WORD in msg):
            return decodeCode.NULL_RECEIVED
        elif (api_code == '0'):
            if tokens[1] == 'F':
                return decodeCode.RESUBMIT_NICKNAME
            elif tokens[1] == 'T':
                self.id  = int(tokens[2])
                return decodeCode.SUBMIT_NICKNAME_SUCCESS
        elif (api_code == '1'):
            self.id = tokens[1]
            self.numberOfPlayers = tokens[2]
            return decodeCode.ORDER_RECEIVED_SUCCESS
        elif (api_code == '2'):
            self.sendToServer('2')
        elif (api_code == '4'):
            self.keywordLength = int(tokens[1])
            self.description = tokens[2]
            return decodeCode.DESCRIPTION_RECEIVED_SUCCESS
        elif (api_code == '5'):  # can xu li them timeout
            self.timeOut = tokens[1]
            self.currentPlayingPlayerID = tokens[3]
            if (self.id == tokens[2]):
                return decodeCode.PREDICT_TURN
        elif (api_code == '6'):
            # player name, their rank, and point
            names = tokens[1].split(',')
            points = tokens[2].split(',')
            self.keyword = tokens[3]
            self.gameTurn = tokens[4]
            self.dashboard = []
            for i in range(0, len(names)):
                self.dashboard.append((names[i],points[i]))
                if self.nickname == names[i]:
                    self.rank = i+1
                    self.point = points[i]
            return decodeCode.UPDATE_DASHBOARD

        elif (api_code == '7'):
            # self.disconnectToServer(self.serverAddress, self.serverPort)
            return decodeCode.QUIT
        return decodeCode.DO_NO_THING


    def displayKeyword(self):
        print(self.keyword)
        # GUI here

    def updateCountDownTimer(self, timeLeft=30):
        if (timeLeft != 30):
            t = self.timeOut
        else:
            t = timeLeft
        while t > 0:
            sys.stdout.write('\rDuration : {}s'.format(t))
            t -= 1
            time.sleep(1)

    def disconnectToServer(self):
        self.soc.close()  # can xem lai cho nay, close thoi da du chua
        return 1

    def connectToServer(self):
        self.soc.connect((self.serverAddress, self.serverPort))
        # self.soc.setblocking(False)
        pass

    def sendToServer(self, msg):
        self.soc.sendall(bytes(msg, 'UTF-8'))
        return True

    def submitNickname(self, nickname):
        self.nickname = nickname
        api_msg = self.encodeMsg((self.API.SEND_NAME.value, nickname))
        print("send nick name:", api_msg)  # use for debugging, will be removed later
        return self.sendToServer(api_msg)

    def submitDisconnect(self):
        api_msg = self.encodeMsg((self.API.SEND_QUIT.value))
        return self.sendToServer(api_msg)

    def submitAnswer(self, letter, keyword):
        api_msg = self.encodeMsg((self.API.SEND_ANSWER.value, letter, keyword))
        print("send letter and keywords:", api_msg)  # use for debugging, will be removed later
        return self.sendToServer(api_msg)

    def readFromSocket(self):
        recv_msg = self.soc.recv(1024)
        if len(recv_msg)>0:
            return recv_msg.decode('UTF-8')
        else: 
            return ''


    def exit(self):
        # TODO: Implement Exit
        api_msg = self.encodeMsg((self.API.SEND_QUIT.value))
        self.sendToServer(api_msg)
        self.soc.close()
        pass


# for debugging purpose, will be remove later
# c = ClientModel('127.0.0.1', 65429)
# c.connectToServer()
# # c.submitNickname(BLANK_WORD)
# # print(c.readFromSocket())
# c.submitNickname("vinh")
# print(c.readFromSocket())
# # # c.updateCountDownTimer(30)
# # ##c.exit()
# # print(c.decodeMsg("0|T|1"))
# t = "absdac/"
# temp = t.split('/')
# for tem in temp:
#     print(len(tem))
