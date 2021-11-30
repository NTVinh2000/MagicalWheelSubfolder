import socket
import selectors

import os
import secrets
import re
import time
import threading

from Server.API import *
from Server.STATE import STATE
from Server.PlayerModel import PlayerModel

from Server.Request.RequestNickname import RequestNickname
from Server.Request.RequestAnswer import RequestAnswer
from Server.Request.BaseRequest import BaseRequest

class ServerModel:

    # constructor
    def __init__(self, totalClient = 2):
        self.HOST = "127.0.0.1"
        self.PORT = 44444
        self.lsock = None

        self.totalClient = totalClient #Total numbers of client can connect to server
        self.clientNum = 0 #Actual number of client connecting to server
        self.nicknameCnt = 0
        self.playerList = []
        
        self.questions = []
        
        self.isRunning = True

        self.hint = ""
        self.keyword = ""
        self.guess = ""
        self.turn = 0
        self.playerAnswerState = STATE.WAITING

        self.minTurn = 2
        self.maxTurn = 5
        self.timeOut = 20
        self.playerIDTurn = -1


    ''' ######## socket functions ######## '''
    def createSocket(self):
        self.lsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP)
        self.lsock.setblocking(False)
        self.lsock.bind((self.HOST, self.PORT))
        self.lsock.listen()
    
    def createSelector(self):
        self.selector = selectors.DefaultSelector()
        self.selector.register(self.lsock, selectors.EVENT_READ, data=None)
        
    def closeConnection(self):
        # đóng server socket
        self.lsock.close()
        self.selector.unregister(self.lsock)

        # remove socket client
        self.removeAllCSockets()
        self.selector.close()


    def removeAllCSockets(self):
        # gửi thông báo đóng đến tất cả client
        disconnectMsg = self.encodeMsg((API_SEND_QUIT))

        for player in self.playerList:
            #TODO: hope it send all in once
            player.socket.send(bytes(disconnectMsg, encoding='UTF-8'))
            self.selector.unregister(player.socket)
            player.socket.close()


    def sendAllClient(self, msg):
        byteMsg = bytes(msg, encoding="UTF-8")
        for player in self.playerList:
            player.msgSent.put(byteMsg)


    def sendToClient(self, player: PlayerModel, msg):
        player.msgSent.put(bytes(msg, encoding="UTF-8"))

    ''' ######## end socket functions ######## '''



    ''' @@@@@@@@ game functions @@@@@@@@ '''

    def loadData(self, path):
        if not os.path.exists(path):
            print("File not found")
            return False

        file = open(path, 'r')
        content = file.readlines()
        file.close()

        if len(content) < 3:
            return False

        total = int(content[0].strip('\n'))
        self.questions = []

        for i in range (total):
            self.questions.append((content[2*i+1].strip('\n'), content[2*i+2].strip('\n')))

        return True


    def chooseKeyword(self):
        tempKey, tempHint = secrets.choice(self.questions)

        while tempKey == self.keyword:
            tempKey, tempHint = secrets.choice(self.questions)

        self.keyword, self.hint = tempKey, tempHint


    def enoughClient(self):
        if self.clientNum == self.totalClient:
            return True
        return False


    def addPlayer(self, socket, addr) -> PlayerModel:
        player = PlayerModel(socket, addr, self.clientNum)
        self.playerList.append(player)
        self.clientNum += 1
        
        return player


    def removePlayer(self, clientAddress, isRemoveSocket = True):
        for player in self.playerList:
            if player.clientAddress == clientAddress:
                sock = player.socket
                self.selector.unregister(sock)
                if isRemoveSocket:
                    sock.close()
                    
                if self.turn > 0:
                    player.isDisconnected = True
                    
                else:
                    self.playerList.remove(player)
                    self.clientNum-=1
                    if player.nickname != '':
                        self.nicknameCnt-=1
                    
                    print("remove player", self.clientNum, self.nicknameCnt, player.nickname)
                return True

        return False


    def validateNickname(self, nickname):
        if len(nickname) > 10:
            return False

        if not re.fullmatch("\w+", nickname):
            return False

        for player in self.playerList:
            if player.nickname == nickname:
                return False

        return True

    
    def canAnswerKeyword(self):
        if self.turn > self.minTurn:
            return True
        return False
            

    def checkKeyword(self, player, keyword):
        if keyword == self.keyword:
            self.guess = self.keyword
            player.addPoint(5)
            return 'T', 5
        
        return 'F', 0
            

    def checkLetter(self, player, guess):
        cnt = 0
        length = len(self.keyword)
        tmp = ""

        for i in range(length):
            c = self.keyword[i]
            if c == guess and self.guess[i] == '*':
                tmp += c
                cnt += 1
            else:
                tmp += self.guess[i]

        if cnt > 0:
            self.guess = tmp
            player.addPoint(1)
            return cnt, 1

        return 0, 0 


    def waitForPlayers(self):
        print("wait for player")
        while self.clientNum < self.totalClient or self.nicknameCnt < self.totalClient:
            pass
        print("end wait for another")

    def sendPlayerOrder(self):
        for i in range(self.clientNum):
            player: PlayerModel = self.playerList[i]
            player.id = i+1 # gán lại thứ tự mới
            player.disqualified = False # cấp lại quyền chơi
            player.point = 0
            orderMsg = self.encodeMsg((API_SEND_ORDER, i+1, self.clientNum))
            self.sendToClient(player, orderMsg)

    def newRound(self):
        self.waitForPlayers()     
        self.sendPlayerOrder()
        self.chooseKeyword()
        self.guess = '*' * len(self.keyword)
        self.playerAnswerState = STATE.WAITING
        self.announcePoint(False)
        self.turn = 1



    def endRound(self):
        self.announcePoint(True)
        self.turn = 0
        self.playerIDTurn = -1
        self.removeDisconnectedPlayers()

    def removeDisconnectedPlayers(self):
        tmp = []
        for player in self.playerList:
            if not player.isDisconnected:
                tmp.append(player)

        self.playerList = tmp
        self.clientNum = self.nicknameCnt = len(self.playerList)

    def announcePoint(self, isRank):
        rankList = []

        if isRank:
            rankList = sorted(self.playerList,
                key= lambda player: player.point, 
                reverse=True)
        else:
            rankList = self.playerList

        nameList = ""
        pointList = ""

        for player in rankList:
            if nameList != "":
                nameList += ","
                pointList += ","

            nameList += player.nickname
            pointList += str(player.point)

        rankMsg = self.encodeMsg((API_SEND_RESULT, nameList, pointList, self.guess, self.turn))
        self.sendAllClient(rankMsg)
        

    def countDown(self):
        tmp = self.timeOut + 1
        while tmp > 0 and self.playerAnswerState == STATE.WAITING:
            time.sleep(1)
            tmp -= 1

        if tmp == 0:
            self.playerAnswerState = STATE.TIMEOUT
            

    def run(self):
        if not self.loadData("database.txt"):
            return

        self.createSocket()
        self.createSelector()

        self.isRunning = True

        # lắng nghe các sự kiện
        listeningThread = threading.Thread(target=self.listening)
        listeningThread.start()

        while self.isRunning:
            # thiết lập ván mới
            self.newRound()
            # gửi câu hỏi mới cho tất cả người chơi
            questionMsg = self.encodeMsg((API_SEND_QUESTION, len(self.keyword), self.hint))
            self.sendAllClient(questionMsg)


            # nếu chưa hết 5 turns hay
            # nếu chơi có ai trả lời đúng keyword
            while self.turn <= self.maxTurn and self.playerAnswerState != STATE.KEYWORD:
                #print("turn: ", self.turn)

                for player in self.playerList:
                    #print("turn: ", self.turn, "player: ", player.nickname)
                    if player.disqualified or player.isDisconnected:
                        continue

                    self.playerAnswerState = STATE.WAITING

                    # mỗi người sẽ đoán tới khi sai
                    while self.playerAnswerState == STATE.WAITING:
                        #print("turn: ", self.turn, "player: ", player.nickname)

                        self.announcePoint(True)

                        # thông báo tới lượt người chơi
                        self.playerIDTurn = player.id
                        turnMsg = self.encodeMsg((API_SEND_IN_TURN, self.timeOut, player.id,player.nickname))
                        self.sendAllClient(turnMsg)

                        #print("before waiting")
                        # đợi người chơi trả lời
                        waitingThread = threading.Thread(target=self.countDown)
                        waitingThread.start()
                        waitingThread.join()
                        #print("after waiting")
                        
                        # nếu người chơi này đoán đúng 1 chữ thì đoán tiếp
                        if self.playerAnswerState == STATE.GUESS:
                            self.playerAnswerState = STATE.WAITING


                    # nếu người chơi đoán đúng thì break turn
                    if self.playerAnswerState == STATE.KEYWORD:
                        break

                # hết toàn bộ mn thì tăng turn lên 1 và bắt đầu lại
                self.turn += 1

            # kết trận
            self.endRound()

            cont = input("Continue (Y/N): ")
            if cont == "N":
                self.isRunning = False


        listeningThread.join()
        self.closeConnection() 


    ''' @@@@@@@@ end game functions @@@@@@@@ '''


    ''' ######## handle request functions ######## '''
    def decodeMsg(self, msg):
        tokens = msg.split('|')
        api_code = tokens[0]

        if (api_code is API_SEND_NAME):
            clientNickname = tokens[1]
            request = RequestNickname()
            request.setData(clientNickname)
            return request

        elif (api_code is API_SEND_ANSWER):
            characterFromClient = tokens[1]
            keywordFromClient = tokens[2]
            request = RequestAnswer()
            request.setData(characterFromClient, keywordFromClient)
            return request

        elif (api_code is API_SEND_QUIT):
            return BaseRequest(API_SEND_QUIT)

        return BaseRequest()


    def encodeMsg(self, tokens):
        apiCode = tokens[0]
        # check to guarantee the sent api msg is right
        if (apiCode is API_SEND_NAME and len(tokens) == 3 or len(tokens) == 2) or (apiCode is API_SEND_ORDER and len(tokens) == 3) or (
                apiCode is API_SEND_CONNECTION and len(tokens) == 1) or (apiCode is API_SEND_ANSWER and len(tokens) == 6) or (
                apiCode is API_SEND_QUESTION and len(tokens) == 3) or (apiCode is API_SEND_IN_TURN and len(tokens) == 4) or (
                apiCode is API_SEND_RESULT and len(tokens) == 5) or (apiCode is API_SEND_QUIT and len(tokens) == 1):
            apiCode = str(apiCode)
            for token in tokens[1:]:
                apiCode += '|' + str(token)

            return apiCode+'/'
        else:
            return ''

    def listening(self):
        while self.isRunning:

            events = self.selector.select(timeout=0.0)
            
            for key, mask in events:

                # khi có kết nối mới từ client
                if key.data is None:
                    #print("server")
                    if self.turn == 0:
                        self.addNewConnection()
                    else: # đang chơi ko nhận thêm
                        self.rejectConnection()
                
                # client cũ gửi gói tin
                else:
                    try:
                        self.serveEvent(key, mask)

                    except Exception as e:
                        #print("exception", e)
                        
                        sock = key.fileobj
                        if self.removePlayer(sock.getpeername()):
                            # self.selector.unregister(sock)
                            # print("nothing")
                            pass

                        self.isRunning = False
                        # self.lsock.shutdown(2)
                        self.lsock.close()
                        break

    def addNewConnection(self):
        #print("add new connection")
        conn, addr = self.lsock.accept()

        # nếu đủ người chơi thì thông báo người mới đã đủ slot và đóng socket
        if self.enoughClient():
            conn.sendall(bytes('Connect Error: Full Slots !!!', encoding="UTF-8"))
            conn.close()
            return

        conn.setblocking(False)

        # nếu chưa đủ người chơi
        playerObj = self.addPlayer(conn, addr)

        events = selectors.EVENT_READ | selectors.EVENT_WRITE
        self.selector.register(conn, events, data=playerObj)

        # tell client that connection is ok
        self.sendToClient(playerObj, "Connected")

    def rejectConnection(self):
        #print("reject new connection")
        conn, addr = self.lsock.accept()

        conn.sendall(bytes('Connect Error: Game has already started !!!', encoding="UTF-8"))
        conn.close()
        
    def serveEvent(self, key, mask):
        sock = key.fileobj
        player: PlayerModel = key.data

        if mask & selectors.EVENT_READ:

            recv_data = sock.recv(1024)
            
            if recv_data:
                #TODO: hope it recv all in once
                self.handleRequest(player, recv_data)

            else:
                if self.removePlayer(player.clientAddress):
                    #('closing connection to', player.clientAddress)
                    pass

        if mask & selectors.EVENT_WRITE:

            if not player.msgSent.empty():
                #TODO: hope it send all in once
                msg = player.msgSent.get()
                sock.send(msg)
                #print("Send to ", player.nickname, ": ", msg)


    def handleRequest(self, player: PlayerModel, data):
        #print("Receive msg from ", player.nickname, ": ", data)
        request = self.decodeMsg(data.decode("UTF-8"))
        

        api = request.api_code
        #print("Request after decode: ", request)

        if api is API_SEND_NAME:
            self.handleCheckNickname(player, request.nickname)
        
        elif api is API_SEND_ANSWER:
            self.handleEvalutateAnswer(player, request)

        elif api is API_SEND_QUIT:
            self.handleQuitGame(player)

        

    def handleCheckNickname(self, player: PlayerModel, nickname):
        responseMsg = ''

        if self.validateNickname(nickname):
            # nếu chưa reg nickname thì tăng biến đếm
            responseMsg = self.encodeMsg((API_SEND_NAME, 'T', player.id))
            if player.nickname == "":
                self.nicknameCnt+=1

            player.nickname = nickname

        else:
            responseMsg = self.encodeMsg((API_SEND_NAME, 'F'))
        
        self.sendToClient(player, responseMsg)


    def handleEvalutateAnswer(self, player: PlayerModel, request):
        #không tới lượt người chơi này
        if player.id != self.playerIDTurn:
            return 

        keyOK = 'F'
        guessOK = 'F'
        point = 0

        cnt, pt = self.checkLetter(player, request.guess)
        if cnt > 0: # đoán đúng từ
            guessOK = 'T'

        if self.canAnswerKeyword() and request.keyword != "":
            # dù đúng hay sai thì lượt nó kết thúc
            player.disqualified = True

            keyOK, point = self.checkKeyword(player, request.keyword)
            if keyOK == 'T': 
                self.playerAnswerState = STATE.KEYWORD
            else:        
                self.playerAnswerState = STATE.WRONG 
                
                
        point += pt

        msgResponse = self.encodeMsg((API_SEND_ANSWER, guessOK, keyOK, point, request.guess, cnt))
        self.sendToClient(player, msgResponse)


        if player.disqualified:
            return

        if guessOK == 'T':
            self.playerAnswerState = STATE.GUESS
        else:
            self.playerAnswerState = STATE.WRONG


    def handleQuitGame(self, player: PlayerModel):
        print("quit game")
        # sock = player.socket

        if self.removePlayer(player.clientAddress, False):    
            # sau khi nhận dc thì gửi về để thông báo ok close đi      
            disconnectMsg = self.encodeMsg((API_SEND_QUIT))
            player.socket.send(bytes(disconnectMsg, encoding="UTF-8"))
            player.socket.close()
            print(player.nickname, " quit ")
            pass
    ''' ######## end handle request functions ######## '''

        
        

            
