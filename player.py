import socket
import threading
import time

'''Welcome to the client side! The player has methods to connect with server and set's its own state.
the functions are pretty much clear.'''

class Player:
    def __init__(self, _id):
        self.MAXLEN = 150  # a unique id for each client
        self.HOST = 'localhost'
        self.PORT = 10000
        self.clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # used to communicate with the server
        self.clientThread = None
        
        self.username = " "
        self.mode = " "
        self.id = _id
        self.state = 1 #available

    def setUsername(self, _username):
        with threading.Lock():
            self.username = _username
    
    def setMode(self, _mode):
        with threading.Lock():
            self.mode = _mode
    
    def setSymbol(self, _symbol):
        with threading.Lock():
            self.symbol = _symbol
	
    def setState(self, _state):
        with threading.Lock():
            self.state = _state
            if self.state == 3:
                self.clientSocket.close()
        print("You have left")
        exit()
    
    # Tries to connect to the sever through mutual port.
    def startConnecting(self):
        try:
            self.clientSocket.connect((self.HOST, self.PORT))
        except socket.error:
            print("Error during connectionnn")
            exit(-1)

    # Uses two threads to send and recieve msg to and from server
    def startCommunicating(self):
        sendThread = threading.Thread(target=self.sendHandler)
        recvThread = threading.Thread(target=self.recvHandler)

        sendThread.start()
        recvThread.start()

        sendThread.join()
        recvThread.join()

    # prints to clinet terminal
    def multiPrint(self, message=""):
        #needs the lock to make sure the right client is getting the message
        with threading.Lock():
            if message:
                print("\33[2K \r" + message)

    def sendHandler(self):
        while True:
            self.multiPrint()
            message = input()
            self.clientSocket.send(message.encode())
            time.sleep(0.5)
            if message == "exit":
                self.setState(3)
                return

    def recvHandler(self):
        while self.state != 3:
            message = self.clientSocket.recv(self.MAXLEN).decode()
            if not message:
                continue
            else:
                self.multiPrint(message)
            print("", end="", flush=True)



client = Player(0)
client.startConnecting()
client.startCommunicating()