#from unicurses import *
from enum import Enum
import d_curses as display
import board
import random
import textwrap
import logging

class Mode(Enum):
    Normal  = 0
    Move    = 1
    EndTurn = 2
    Melee   = 3

player1name = "Player One"
player2name = "Player Two"

def randomBoard(theBoard):
    for y in range(0,board.Board.HEIGHT):
        for x in range(0,board.Board.WIDTH//2):
            tl = (board.Tile.Ground,board.Tile.Ground,board.Tile.Ground,board.Tile.Wall,board.Tile.Wall,
                  board.Tile.Ground,board.Tile.Ground,board.Tile.Ground,
                  board.Tile.Ground,board.Tile.Ground,board.Tile.Ground,board.Tile.Ground,board.Tile.Ground,
                  board.Tile.Door,  board.Tile.Window,board.Tile.Brambles,
                  board.Tile.Water, board.Tile.Tree)
            tt = random.choice(tl)
            theBoard.board[theBoard.coord(x,y)] = tt
            theBoard.board[theBoard.coord(board.Board.WIDTH-x-1,y)] = tt

class Game:
    def __init__(self):
        self.cursX = 0
        self.cursY = 0
        self.selected = None # the currently selected player
        self.mode = Mode.Normal
        self.board = None

    def setupData(self):
        self.board = board.Board()
        self.dicelog = self.board.log
        t = board.PlayerType(0,"swordsman")
        self.board.addType(t)
        t = board.PlayerType(1,"archer")
        self.board.addType(t)

        randomBoard(self.board)
        for i in range(0,20):
            x = -1
            y = -1
            while not self.board.isOpen(x,y):
                x = random.randint(0,board.Board.WIDTH-1)
                y = random.randint(0,board.Board.HEIGHT-1)
            p = board.Player(self.board.getType(i%2))
            p.x = x
            p.y = y
            p.side = (i % 2)
            self.board.players.append(p)


    def drawUI(self):
        gameBoard = self.board
        display.reset()
#        display.clear()

        # paint UI frame
        display.highlight()
        for i in range(49, 80):
            display.mvchar(i, 0, " ")
        display.mvstring(50, 0, "Tactics!")

        display.reset()
        for y in range(0, 24):
            display.mvchar(48, y, "|")

        for x in range(49, 80):
            display.mvchar(x, 4, "-")
        display.mvchar(48, 4,"+")

        # paint map
        for y in range(0, board.Board.HEIGHT):
            for x in range(0, board.Board.WIDTH):
                display.reset()
                if x == self.cursX and y == self.cursY:
                    display.highlight()
                p = gameBoard.playerAt(x,y)
                if p != None:
                    if p.side == 0:
                        display.color(display.BRIGHTBLUE)
                    else:
                        display.color(display.BRIGHTRED)
                    if p.posture == board.Posture.Prone:
                        display.mvchar(x*2,y,"p")
                    elif p.action == board.Action.Move:
                        display.mvchar(x*2,y,"m")
                    else:
                        display.mvchar(x*2,y,str(p.side+1))
                else:
                    tt = gameBoard.at(x,y)
                    if tt == board.Tile.Ground:
                        display.mvchar(x*2,y,".")
                    elif tt == board.Tile.Wall:
                        display.mvchar(x*2,y,"#")
                    elif tt == board.Tile.Tree:
                        display.mvchar(x*2,y,"T")
                    elif tt == board.Tile.Door:
                        display.mvchar(x*2,y,"+")
                    elif tt == board.Tile.Water:
                        display.mvchar(x*2,y,"~")
                    elif tt == board.Tile.Brambles:
                        display.mvchar(x*2,y,"^")
                    elif tt == board.Tile.Window:
                        display.mvchar(x*2,y,"=")
                    else:
                        display.mvchar(x*2,y,"?")
                display.reset()
                display.mvchar(x*2+1,y, " ")

        # paint dice log
        display.reset()
        for i in range(19):
            m = self.dicelog.get(i)
            display.mvstring(49, 23-i, "{:30}".format(m))

        # paint turn info
        display.highlight()
        global player1name, player2name
        currentPlayerName = player1name
        if gameBoard.turn == 1:
            currentPlayerName = player2name
        display.mvstring(60,0, "Turn {} {}".format(gameBoard.turnno, currentPlayerName))
        display.reset()

        # paint highlighted space info
        phere = gameBoard.playerAt(self.cursX, self.cursY)
        if phere == None:
            display.mvstring(49, 1, "                              ")
            display.mvstring(49, 2, "                              ")
        else:
            pname = []
            pname.append(phere.name)
            pname.append(" (")
            pname.append(phere.type.name)
            if phere.posture == board.Posture.Prone:
                pname.append(") - Prone")
            elif phere.action == board.Action.Start:
                pname.append(")")
            else:
                pname.append(") - ")
                pname.append(phere.action.name)
            display.mvstring(49, 1, "".join(pname))

            display.mvstring(49, 2, "M{}/{} C{} S{} R{} P{} E{} H{}/{} D{}".format(
                                    phere.moved, phere.type.move,
                                    phere.type.combat, phere.type.strength,
                                    phere.type.ranged, phere.type.power,
                                    phere.type.evade, phere.health,
                                    phere.type.health, phere.type.defense))
        display.mvstring(49, 3, "                              ")
        display.mvstring(49, 3, self.mode.name)
        display.mvstring(80-len(gameBoard.at(self.cursX,self.cursY).name),
                            3, gameBoard.at(self.cursX,self.cursY).name)

        # paint game status
        display.mvstring(51, 4, " Units: {} ".format(gameBoard.unitCount()))
        display.mvstring(63, 4, " Avail: {}/{} ".format(gameBoard.unitsUnmoved(gameBoard.turn),
                                                      gameBoard.unitCount(gameBoard.turn)))

        # all done; update screen
        display.paint()

    def keyToDir(self, key):
        if key == display.RIGHT or key == ord("d"):
            return board.Direction.East
        if key == display.DOWN or key == ord("x"):
            return board.Direction.South
        if key == display.LEFT or key == ord("a"):
            return board.Direction.West
        if key == display.UP or key == ord("w"):
            return board.Direction.North
        if key == key == ord("q"):
            return board.Direction.Northwest
        if key == key == ord("e"):
            return board.Direction.Northeast
        if key == key == ord("c"):
            return board.Direction.Southeast
        if key == key == ord("z"):
            return board.Direction.Southwest
        return None

    def main(self):
        b = self.board

        while True:
            self.drawUI()
            key = display.getkey()

            if key == ord("Q"):
                break;

            elif self.mode == Mode.Normal:
                dir = self.keyToDir(key)
                if dir != None:
                    nx, ny = b.shift(self.cursX, self.cursY, dir)
                    if b.valid(nx, ny):
                        self.cursX = nx
                        self.cursY = ny
                elif key == 10:
                    self.mode = Mode.EndTurn

                elif key == ord("m"):
                    selected = b.playerAt(self.cursX, self.cursY)
                    if selected != None:
                        if selected.side == self.board.turn and selected.action == board.Action.Start:
                            self.mode = Mode.Move
                            self.dicelog.add("Moving " + selected.name + "...")
                elif key == ord("t"):
                    selected = b.playerAt(self.cursX, self.cursY)
                    if selected != None:
                        if selected.side == self.board.turn and selected.action == board.Action.Start:
                            self.mode = Mode.Melee
                            self.dicelog.add(selected.name + " initiating melee attack...")


            elif self.mode == Mode.EndTurn:
                if key == 10:
                    self.board.endTurn()
                self.mode = Mode.Normal

            elif self.mode == Mode.Move:
                dir = self.keyToDir(key)
                if dir != None:
                    if b.tryMove(selected, dir) == board.Result.Bad:
                        self.mode = Mode.Normal
                    self.cursX = selected.x
                    self.cursY = selected.y
                elif key == 10:
                    self.mode = Mode.Normal
                    if selected.moved == 0:
                        self.dicelog.add("Cancelled")
                    selected = None

            elif self.mode == Mode.Melee:
                dir = self.keyToDir(key)
                if dir != None:
                    tx, ty = b.shift(selected.x, selected.y, dir)
                    if b.playerAt(tx,ty) != None:
                        if b.tryAttack(selected, dir) != board.Result.Cant:
                            self.mode = Mode.Normal
                elif key == 10:
                    self.mode = Mode.Normal
                    if selected.moved == 0:
                        self.dicelog.add("Cancelled")
                    selected = None


try:
    logging.basicConfig(filename="tactics.log",
                        format='%(levelname)s:%(message)s',
                        filemode="w",
                        level=logging.DEBUG)
    logger = logging.getLogger()
    display.start()
    game = Game()
    game.setupData()
    game.main()
finally:
    display.end()
