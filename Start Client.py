from Client.GUI import GUI
from Client.Constants import *
import threading
from Client.ClientModel import ClientModel
from Client.decodeCode import  decodeCode
import queue


HOST = '127.0.0.1'  # Standard loopback interface address (localhost)
PORT = 44444
sampleClientModel = ClientModel(HOST, PORT)
my_queue = queue.Queue()


def main():


   sampleClientModel.connectToServer()

   msg_received = sampleClientModel.readFromSocket()
   print("After connect receicve:",msg_received)
   sampleResultList = {'Alice':(5, 10), 'Alex':(3, 10), 'John':(6, 10), 'Bob':(4, 10), 'Bill':(7, 10),
             'Mike':(1, 10), 'Susan':(8, 10), 'Carol':(2, 10), 'Lion':(10, 10), 'Ryan':(9, 10)}


   # ALWAYS start 1 GUI at a thread
   gameGUI = GUI()
   isGameDone = False

   print(gameGUI)


   threadGUI = threading.Thread(target=gameGUI.game_loop)
   threadGUI.start()
   print("GUI run 103", gameGUI.run)

   if msg_received != "Connected":
      #nếu ko connected dc thì display màn hình end game -> full slot
      gameGUI = GUI()
      output = gameGUI.get_output_from_state(STATE_END)
      return


   def listenServer():
      print("heello", gameGUI.run)
      cnt = 0

      while gameGUI.is_alive() != False:
         print(cnt)
         cnt +=1
         msg = sampleClientModel.readFromSocket()

         # server shutdown
         if msg == "":
            return

         api_codes = msg.split('/')
         for api_code in api_codes:
            if(len(api_code)>0):
               my_queue.put(api_code)

      print("hallo", gameGUI.run)
      # threadGUI.join()
      return
               
   threadListening = threading.Thread(target=listenServer)
   threadListening.start()

   def checkSystemClose(content):
      print("Check close", content)
      if content == 'SYSCLOSESYS':
         # thông báo client thoát         
         sampleClientModel.submitDisconnect()

         # # join thread gui
         threadGUI.join()

         # # join thread nghe
         threadListening.join()

         # thread nghe join thì server đã đọc gói disconnect
         # v có thể gửi 0 bytes lên để disconnect
         sampleClientModel.disconnectToServer()

         print('Main thread end')
         return True
      return False

   # Take nickname input
   output = gameGUI.get_output_from_state(STATE_REGISTER)
   if checkSystemClose(output):
      print(72)
      return

   print('Output: ' + output)
   sampleClientModel.submitNickname(output)
   while True:

      if my_queue.empty() == False:
         msg_received = my_queue.get()
         if len(msg_received) > 1:
            print("message received:", msg_received)
            msg_decoded = sampleClientModel.decodeMsg(msg_received)
            print("message decoded:", sampleClientModel.decodeMsg(msg_received))

            if msg_decoded == decodeCode.RESUBMIT_NICKNAME or msg_decoded == decodeCode.NULL_RECEIVED:
               output = gameGUI.get_output_from_state(STATE_REGISTER, error_message=ERROR_MESSAGE_REGISTER)
               if checkSystemClose(output):
                  print(105)
                  return
                  
               print("resubmit nickname:", output)
               sampleClientModel.submitNickname(output)
            elif msg_decoded == decodeCode.SUBMIT_NICKNAME_SUCCESS:
               break
      else: pass
   print("pass the submit nickname process")



   output = gameGUI.get_output_from_state(STATE_COMPLETE_REGISTER)
   

   flag = False
   while True:
      if my_queue.empty() == False:
         flag = True
         msg = my_queue.get()
         msg_decoded = sampleClientModel.decodeMsg(msg)
         print("msg received:",msg)
         print("msg decoded:",msg_decoded)
         if msg_decoded == decodeCode.PREDICT_TURN:

            countDown =  int(sampleClientModel.timeOut)
            gameGUI.set_count_down(countDown)
            gameGUI.get_output_from_state(STATE_WAIT_WITHOUT_COUNT, model=sampleClientModel)
            
            letterInput = gameGUI.get_output_from_state(STATE_PLAY_LETTER, model=sampleClientModel,result_list= sampleClientModel.dashboard)
            sampleClientModel.guessLetter = letterInput
            
            if checkSystemClose(letterInput):
               print(141)
               return   

            keywordInput = ''
            if int(sampleClientModel.gameTurn) >= 3:
               keywordInput = gameGUI.get_output_from_state(STATE_PLAY_WORD, model=sampleClientModel,result_list= sampleClientModel.dashboard)

            if keywordInput == BLANK_WORD:
               keywordInput = ''
           
            if checkSystemClose(keywordInput):
               print(152)
               return   

            sampleClientModel.submitAnswer(letterInput,keywordInput)
            output = gameGUI.get_output_from_state(STATE_WAIT_WITHOUT_COUNT, model=sampleClientModel,result_list= sampleClientModel.dashboard)
            print("output from state wait without count",output)
         
         elif msg_decoded ==  decodeCode.UPDATE_DASHBOARD:
            # output = gameGUI.get_output_from_state(STATE_VIEW_RESULT, result_list=sampleClientModel.dashboard)
            print("Dashboard")
            for i in range(0,len(sampleClientModel.dashboard)):
               print("Rank:",i," Player:",sampleClientModel.dashboard[i][0]," Point:",sampleClientModel.dashboard[i][1])
            output = gameGUI.get_output_from_state(STATE_WAIT_WITHOUT_COUNT, model=sampleClientModel,result_list= sampleClientModel.dashboard)
            print("output from state wait without count", output)
         
         # nếu nhận được thông báo nghỉ chơi từ server
         elif msg_decoded == decodeCode.QUIT:
            isGameDone = True
            # display end gui
            output = gameGUI.get_output_from_state(STATE_END)
            # close socket
            sampleClientModel.disconnectToServer()
            # join thread listen server
            threadListening.join()
            #đợi tắt GUI
            threadGUI.join()
            return
            

         else:
            output = gameGUI.get_output_from_state(STATE_WAIT_WITHOUT_COUNT, model=sampleClientModel,result_list= sampleClientModel.dashboard)
            print("go into else")
            print(output)

      if not gameGUI.is_alive():
         checkSystemClose('SYSCLOSESYS')
         # if output == 'SYSCLOSESYS' or not gameGUI.is_alive():
         #    threadGUI.join()
         #    threadListening.join()
         #    sampleClientModel.disconnectToServer()
         #    print('Main thread end 169')
         #    # SystemExit()
         #    return
      # if my_queue.empty() == True and flag ==True:
      #    break

   output = gameGUI.get_output_from_state(STATE_WAIT_WITHOUT_COUNT, model=sampleClientModel)
   print(sampleClientModel.dashboard)


   print("Pass receive api 1 and 3")

   #game start here
   # while True:
   #    msg_received = sampleClientModel.readFromSocket()
   #    if len(msg_received)>=1 :
   #       print("message received:",msg_received)
   #       msg_decoded = sampleClientModel.decodeMsg(msg_received)
   #       print("message decoded:",sampleClientModel.decodeMsg(msg_received))
   #       if msg_decoded == decodeCode.PREDICT_TURN :
   #          gameGUI.set_count_down(sampleClientModel.timeOut)
   #          #output = gameGUI.get_output_from_state(STATE_WAIT, model=sampleClientModel)
   #          letter = gameGUI.get_output_from_state(STATE_PLAY_LETTER, model=sampleClientModel)
   #          print('Output: ' + output)
   #          keyword = gameGUI.get_output_from_state(STATE_PLAY_WORD, model=sampleClientModel)
   #          print('Output: ' + output)
   #          sampleClientModel.submitAnswer(letter,keyword)
   #    else:
   #       pass

   # #
   # # # Game play: take 1 letter
   # # # NOTE: This function require ClientModel, if not, it will not display anything
   # gameGUI.set_count_down(10)    # count down time = 10s
   # output = gameGUI.get_output_from_state(STATE_PLAY_LETTER, model=sampleClientModel)
   # print('Output: ' + output)
   # #
   # # # Game play: take keyword
   # # # NOTE: This function require ClientModel, if not, it will not display anything
   # gameGUI.set_count_down(10)  # count down time = 10s
   # output = gameGUI.get_output_from_state(STATE_PLAY_WORD, model=sampleClientModel)
   # print('Output: ' + output)
   # #
   # #
   # # # View result
   # # # NOTE: This function require the player list, if not, it will display nothing
   # # # NOTE: Output has no meaning because this screen is to display only
   # output = gameGUI.get_output_from_state(STATE_VIEW_RESULT, result_list=sampleResultList)
   # print('Output: ' + output)
   #
   #
   # # output == 'SYSCLOSESYS' means player closed the game window
   # # is_alive() is a function to check if a GUI window is running or not
   # # The author suggests to use both condition as below to prevent potential asyncronous problems (The author tried to fix and did not meet these problems but safety is important)
   if output == 'SYSCLOSESYS' or not gameGUI.is_alive():
      threadGUI.join()
      sampleClientModel.disconnectToServer()
      print('Main thread end')
      SystemExit()
      return

main()