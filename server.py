import socket
import threading
import time
from game import XOGame
import select

''' Welcome to the server side! the serverhas its own functions to handle client and the game and on top of that
if has the ClientServer() object which is a client (player) object made in the server side to handle and 
store necessary information about the client'''

class ClientServer():
    # Initializes main attributes of the object
    def __init__(self, _id, _clientSocket):
        self.id = _id # a unique id for each client
        self.clientSocket = _clientSocket # used to communicate with the client
        self.username = "?"
        self.clientThread = None
        self.mode = 0 # can be 3, 4, or 5 to show 3 modes of the game, namely (3x3), (4x4) and (5x5) grid
        self.state = 0 # can be 0, 1, or 3 indicating available, busy, exited states, respectively.
        self.Lock1 = threading.Lock()

    # Sets client's game mode
    def setMode(self, _mode):
        # Uses a lock to change mode of each client-server object
        # as each client thread may access it at the same time
        with self.Lock1:
            self.mode = _mode
    
    def setUsername(self, _username):
        with self.Lock1:
            self.username = _username
    
    # Sets client state (available, playing, exited)
    def setState(self, _state):
        with self.Lock1:
            self.state = _state
    

class Server():
    def __init__(self):
        self.MAXLEN = 150 # length of data being recieved or sent
        self.HOST = 'localhost'
        self.PORT = 10000
        self.serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        self.uniqueClientID = 0
        self.uniqueGameID = 0
        self.clients = {} #stores online players as dictionary clinent-id -> player-obj
        self.gameList = {} #stores ongoing games as dictionary game-id -> [player-obj1, player-obj2]
        
        self.clientLock = threading.Lock()
        self.stateLock = threading.Lock()
        self.Lock3 = threading.Lock()

    ''' To handle a scenario where player inputs (which are sent through a socket) are captured
    and buffered for later execution — specifically where inputs should not affect the game state 
    when it is not the players turn. If in any state the client want to exit, this function will
    handle it and informs server that the client has left by self.setState() function.'''
    def flushClientBuffer(self, clientSocket):
        TIMEOUT = 0.01
        value = True
        while True:
            ready_to_read, _, _ = select.select([clientSocket], [], [], TIMEOUT)
            if ready_to_read:
                data = clientSocket.recv(1024)
                if data == 'exit':
                    clientSocket.setState(3)
                    value = False
                    break
                if not data:
                    break 
            else:
                break
        return value

    # Function to start listening for clients
    def startListening(self):
        try:
            self.serverSocket.bind((self.HOST, self.PORT))
        except socket.error:
            print ('Bind Failed')
            exit()
        self.serverSocket.listen(5)
        self.multiPrint("*** Listening ***");  
 
    # Function to accept a client if is has been requested
    def startAccepting(self):
        while True:
            clientSocket, addr = self.serverSocket.accept()
            print(f"Accepted connection from {addr}, {clientSocket}")
            self.uniqueClientID += 1
            clientServer = ClientServer(self.uniqueClientID, clientSocket)
            clientServer.clientThread = threading.Thread(target=self.handleClient, args=(clientServer,))
            clientServer.clientThread.start()
    
    # Function to add client to the list
    def addClient(self, clientServer):
        # Definitely needs lock as two client and their id's must not be mixed up!
        with threading.Lock():
            self.clients[clientServer.id] = clientServer
    
    # Function to delete client from the list and close the connection between server and the client
    def endConnection(self, clientServer):
        time.sleep(1)
        # When the client leaves, the new player can acquire the prev one username without any
        # problem. This is achieved with the lock
        with threading.Lock():
            if clientServer.id in self.clients:
                del self.clients[clientServer.id]
            clientServer.clientSocket.close()
        print(f"{id} has left")

    def closeConnection(self):
        self.serverSocket.close()

    # Prints to server terminal
    def multiPrint(self, str):
        with threading.Lock():
            print(str)

    # Sends msg to client if the client has not exited
    def sendMessage(self, _clientSocket, message):
        if (_clientSocket):
            _clientSocket.send(message.encode('utf-8'))

    # the function is called by handleClient() function
    def loginClient(self, clientServer):
        self.sendMessage(clientServer.clientSocket, "> Welcome to TIC TAC TOE, Choose a username: ")
        username = ''
        while(True):
            username = clientServer.clientSocket.recv(self.MAXLEN).decode()
            if not username:
                return False
            flag = True
            # time sleep for the list to be updated if needed because it is happening in a loop
            time.sleep(0.01)
            for player in self.clients:
                if self.clients[player].username == username:
                    flag = False
                    break
            if not flag:
                self.sendMessage(clientServer.clientSocket, "> This username is already taken, try again.")
                continue
            else:
                #sets username and adds the client to the online players
                clientServer.setUsername(username)
                self.sendMessage(clientServer.clientSocket, f"> Hi {username}!")
                self.addClient(clientServer)
                print(f"{username} has joined with {self.clients[clientServer.id].username}")
                return True
    
    def handleClient(self, clientServer):
        if not self.loginClient(clientServer):
            self.endConnection(clientServer)
            return
        self.handleClientReq(clientServer)
    
    def handleClientReq(self, clientServer):
        while (clientServer.clientSocket):
            self.sendMessage(clientServer.clientSocket, "> Choose a mode:\n [3]: 3x3\n [4]: 4x4\n [5]: 5x5")
            mode = clientServer.clientSocket.recv(self.MAXLEN).decode()
            if not mode:
                continue
            
            if mode == "exit":
                self.endConnection(clientServer)
                continue

            elif int(mode) < 3 or int(mode) > 5:
                self.sendMessage(clientServer.clientSocket, "> Out of range.")
                continue
            break
        clientServer.setMode(int(mode))
        
        while (True):
            self.sendMessage(clientServer.clientSocket, "> Set your state:\n [A]: Available\n [B]: Busy\n [exit]: Logout")
            state = clientServer.clientSocket.recv(self.MAXLEN).decode()
            if not state:
                continue
            if state == "exit":
                self.endConnection(clientServer)
                return
            elif state == 'B': #busy, nothign else to do except to see the game list :)
                self.sendMessage(clientServer.clientSocket, "> See the game list?")
                ans = clientServer.clientSocket.recv(self.MAXLEN).decode()
                if ans == 'y':
                    self.showGameList(clientServer.clientSocket)
                continue
            elif state == 'A': #client ready to play!
                break
            else:
                self.sendMessage(clientServer.clientSocket, "> None of the above were chosen, try again.")
        clientServer.setState(1)
        self.sendMessage(clientServer.clientSocket, "> Waiting for opponent...")
        self.reqOpponent(clientServer)
            
    def showGameList(self, clientSock):
        msg = "> Ongoing Games:"
        g = ''
        for games in self.gameList:
            g += "\n Game ID:" + str(games) + " | Players: " + self.gameList[games][0].username + " vs " + self.gameList[games][1].username
        if g == '':
            g = "\n Empty"
        self.sendMessage(clientSock,  msg + g + "\n")

    # matches two available players wiht the same game mode
    def reqOpponent(self, clientServer):
        p1 = clientServer
        p2 = None
        self.flushClientBuffer(p1.clientSocket)
        # loops till finds an available opponent
        for opponents in self.clients:
            opp = self.clients[opponents]
            if opp.username != p1.username and opp.state == 1 and p1.state == 1 and p1.mode == opp.mode:
                p2 = opp
                break
        if p2 == None:
            # if not found, sleeps and tries again
            time.sleep(1) 
            self.reqOpponent(p1)
        else:
            # opponents are matched and their states are set to busy so no other
            # waiting player can have these two as their opponent
            p1.setState(0)
            p2.setState(0)
            self.initializeGame(p1, p2)
            # ending the game
            self.sendMessage(p1.clientSocket, "The game has ended, login again to play another game")
            self.sendMessage(p2.clientSocket, "The game has ended, login again to play another game")
            time.sleep(2)
            self.endConnection(p1)
            self.endConnection(p2)
            
    def initializeGame(self, p1, p2):
        self.uniqueGameID += 1
        game = XOGame(p1.mode, self.uniqueGameID, p1.username, p2.username)
        print (f"New Game with id: {id}")
        self.gameList[game.gameID] = [p1.username, p2.username]
        
        self.sendMessage(p1.clientSocket, "> OPPONENT FOUND! " + p1.username + " VS " + p2.username)
        self.sendMessage(p2.clientSocket, "> OPPONENT FOUND! " + p2.username + " VS " + p1.username)
        
        haveWinner = False
        #while none of the players have exited do...
        while (p1.state != 3 and p2.state != 3):
            # the turn is set in the game.py so the server need to get the turns from the game and
            # save it for its own
            if (game.turn.username == game.p1.username):
                turn = p1
                notturn = p2
            else:
                turn = p2
                notturn = p1
            # to implement GUI, no time :(
            '''cursor = 'x' if self.turn.symbol == 'X' else 'circle'
            self.window.TKroot.config(cursor=cursor)
            event, values = self.window.read()
            if event == sg.WINDOW_CLOSED:
                break
            
            self.window['stat'].update(self.status)
            self.makeMove(event)'''

            print(game.status)
            print(game.turn.username)
            print(game.notturn.username)
            brd = game.showBoard()
            #we want the boards to be sent first and then the status, so => lock!
            with threading.Lock():
                self.sendMessage(turn.clientSocket, brd)
                self.sendMessage(notturn.clientSocket, brd)
            self.sendMessage(turn.clientSocket, "> Your turn, MOVE: ")
            self.sendMessage(notturn.clientSocket, "> NOT your turn, wait for the opponent to make a move... ")

            # checks the move and proceeds if valid
            while (True):
                inp = turn.clientSocket.recv(self.MAXLEN).decode()
                if not inp:
                    exit()
                if inp == 'exit':
                    turn.setState(3)
                    break

                x, y = inp.split(" ") 
                x = int(x)
                y = int(y)
                
                if not self.isValid(game, x, y):
                    self.sendMessage(turn.clientSocket, "> Invalid move.")
                    continue
                else:
                    break
            
            a = self.flushClientBuffer(p1.clientSocket)
            b = self.flushClientBuffer(p2.clientSocket)
            if not a or not b or turn.state == 3:
                break
            
            game.makeMove((x, y))
            
            if game.over:
                haveWinner = True
                break
               
                '''self.window['stat'].update(self.status)
        self.window.close()'''
        #checks if the game has winner or someone has left
        if haveWinner:
            print(game.status)
            self.sendMessage(turn.clientSocket, game.status)
            self.sendMessage(notturn.clientSocket, game.status)
            game.showBoard()
        else:
            plyr1 = p1 if p1.state == 3 else p2
            plyr2 = p2 if plyr1 == p1 else p1
            print(f"{plyr1} exited!")
            self.sendMessage(plyr2.clientSocket, "Opponent died!")
            
        #delets the game when done
        with threading.Lock():
            if game.gameID in self.gameList:
                del self.gameList[game.gameID]
    
    # checks if the move is in range and the grid is empty
    def isValid(self, game, x, y):
        if x >= game.mode or y >= game.mode or x < 0 or y < 0 or game.board[x][y] != '-':
            return False
        return True


server = Server()
server.startListening()
server.startAccepting()
            
