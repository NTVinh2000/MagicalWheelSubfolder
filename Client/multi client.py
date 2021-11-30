import socket
import threading
import time
import queue

my_queue = queue.Queue()


def getUserInput():
    while True:
        tmp = input()
        if (len(tmp)):
            my_queue.put(tmp)
        if tmp == 'quit':
            break

def listenServer():
    global message, s
    while True:
        recv_msg = s.recv(4096)
        message = repr(recv_msg)
        if len(message) > 4:
            message = str(message[2:-1])
            print(message)
            break


if __name__ == '__main__':
    t1 = threading.Thread(target=getUserInput)
    t2 = threading.Thread(target=listenServer)
    HOST = '127.0.0.1'
    PORT = 65429
    message = None

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        t2.start()
        t2.join()
        t1.start()

        while True:
            if my_queue.empty() == False:
                inp = my_queue.get()
                print(inp)

                if inp == 'quit' or message == 'Connect Error: Full Slots !!!':
                    print('''Type 'quit' to exit!''')
                    s.close()
                    exit(1)
                else:
                    # code except Input stream here
                    s.sendall(str.encode(inp))
                    recv_msg = s.recv(4096)
                    print("Receive", repr(recv_msg))
