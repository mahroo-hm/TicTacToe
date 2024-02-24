import PySimpleGUI as sg

'''This is the main X-O game, turns and loss/win is calculated within this file and only the server has access to it.'''

#Player object of game file to acess to some player's information
class Player:
    def __init__(self, _username, _symbol):
        self.username = _username
        self.symbol = _symbol
        self.state = 1 #available

class XOGame():
    # gets the gameid, user name of player 1 and 2 that the server has decided to play with eachother
    def __init__(self, _mode, _gameID, _p1, _p2):
        self.gameID = _gameID
        self.mode = _mode #sets the mode to build the grid and winning combination for it
        self.over = False

        self.p1 = Player(_p1, "X") #sets symbols
        self.p2 = Player(_p2, "O")
        self.turn = self.p1 #sets turns
        self.notturn = self.p2
        self.status = self.turn.username + "'s Turn" #used in gui and server can access it to print in its terminal
        
        self.setBoardLayout() # for gui purposes
        self.winningCombinations = self.generateWinningCombinations() # stores all winning compositions of the chosen mode
        '''self.window = sg.Window(title = self.gameID, layout = self.gridLO + self.statLO, margins=(100, 100)).Finalize()'''
    
    def setBoardLayout(self):
        self.board = [["-" for i in range(self.mode)] for j in range(self.mode)]
        self.gridLO = [[sg.Button('', size=(2, 2), key=(i, j), font = ('Helvetica', 15)) for j in range(self.mode)] for i in range(self.mode)]
        self.statLO = [[sg.Text('STAT', key = 'stat', font = ('Helvetica', 20), justification = 'center', expand_x = True)]]

    #Changes turn based on previous turn
    def changeTurns(self):
        self.turn = self.p2 if self.turn == self.p1 else self.p1
        self.notturn = self.p2 if self.turn == self.p1 else self.p1

    # updates status test, if the game is over it sets the flag
    def updateStatusText(self):
        x = self.isGameOver()
        if x == 0:
            self.status = self.turn.username + "'s Turn"
            self.over = False
        elif x == 1:
            self.changeTurns()
            self.status = self.turn.username + " Won!"
            self.over = True
        else:
            self.status = "Draw"
            self.over = True
    

    def isGameOver(self):
        fin = True
        win = False
        #checks if a winnig combination is reached
        for x in self.winningCombinations:
            if self.board[x[0][0]][x[0][1]] == self.board[x[1][0]][x[1][1]] == self.board[x[2][0]][x[2][1]] != '-':
                if self.mode != 5:
                    win = True
                    break
                # in (5x5) grid the winnig comb consists of 4 cells
                elif self.board[x[0][0]][x[0][1]] == self.board[x[3][0]][x[3][1]]:
                    win = True
                    break
        if win:
            # return 1 if a winning combination has been reached by the one player
            return 1
        
        # checks if thereis still an empty cell in the grid
        for i in range(self.mode):
            for j in self.board[i]:
                if j == '-':
                    fin = False
                    break
            if fin == False:
                break
        if fin:
            # none are empty so the game is a draw
            return 2
        # game will go on...
        return 0

    # function to print the game board
    def showBoard(self):
        brd = ''
        for x in self.board:
            print(x)
            for y in x:
                brd += y
                brd += ' '
            brd += "\n"
        return brd

    # function to know if a player has exited
    def changeState(self, _p, _state):
        if _p == self.p1.username:
            self.p1.state = _state
        else:
            self.p2.state = _state
   
    # this function is never called in the server, the server does the function inside itself. 
    # the purpose was to test the game if wokrs alright
    def startGame(self):
        while (True):
            #checks if any player has logged out
            if (self.p1.state == 3):
                return 1
            elif (self.p2.state == 3):
                return 2

            '''cursor = 'x' if self.turn.symbol == 'X' else 'circle'
            #self.window.TKroot.config(cursor=cursor)
            event, values = self.window.read()
            if event == sg.WINDOW_CLOSED:
                break
            
            self.window['stat'].update(self.status)
            self.makeMove(event)'''

            print(self.status)
            self.showBoard()
            # the move has been checkes by the server
            x, y = input("move ").split(" ")
            self.makeMove((int(x), int(y)))

            if self.over:
                print(self.status)
                self.showBoard()
                return 0
                '''self.window['stat'].update(self.status)
        #self.window.close()'''

    #makind a vallid move
    def makeMove(self, event):
        x = event[0]
        y = event[1]
        if self.board[x][y] == '-':
            self.board[x][y] = self.turn.symbol
            #self.window[event].update(self.turn.symbol)
            self.changeTurns()
            self.updateStatusText()   
    
    # generated winnign combinations for the grid return an array of tupples
    def generateWinningCombinations(self):
        boardSize = self.mode
        consecutiveCnt = self.mode if self.mode == 3 else self.mode - 1
        w = []
        # Winning Rows
        for row in range(boardSize):
            for col in range(boardSize - consecutiveCnt + 1):
                w.append([(row, col + i) for i in range(consecutiveCnt)])
        
        # Winning Columns
        for col in range(boardSize):
            for row in range(boardSize - consecutiveCnt + 1):
                w.append([(row + i, col) for i in range(consecutiveCnt)])
                
        # Winning Diagonals (top-left to bottom-right)
        for row in range(boardSize - consecutiveCnt + 1):
            for col in range(boardSize - consecutiveCnt + 1):
                w.append([(row + i, col + i) for i in range(consecutiveCnt)])
                
        # Winning Diagonals (top-right to bottom-left)
        for row in range(boardSize - consecutiveCnt + 1):
            for col in range(consecutiveCnt - 1, boardSize):
                w.append([(row + i, col - i) for i in range(consecutiveCnt)])
        
        return w
    