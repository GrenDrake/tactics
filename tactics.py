#from unicurses import *
from enum import Enum
import d_curses as display
import random
import textwrap
import logging

class Direction(Enum):
    North     = 0
    Northeast = 1
    East      = 2
    Southeast = 3
    South     = 4
    Southwest = 5
    West      = 6
    Northwest = 7
class Mode(Enum):
    Normal  = 0
    Move    = 1
    EndTurn = 2
    Melee   = 3
class Action(Enum):
    Start   = 0
    Move    = 1
    Attack  = 2
class Tile(Enum):
    Ground   = 0
    Tree     = 1
    Wall     = 2
    Door     = 3
    Window   = 4
    Water    = 5
    Brambles = 6
    Capture  = 7
class Result(Enum):
    Good = 0
    Bad  = 1
    Cant = 2
class Posture(Enum):
    Standing = 0
    Prone = 1

player1name = "Player One"
player2name = "Player Two"

class PlayerType:
    def __init__(self, ident, name):
        self.ident = ident
        self.name = name
        self.move = 5
        self.combat = 3
        self.strength = 3
        self.ranged = 0
        self.power = 0
        self.evade = 0
        self.health = 5
        self.defense = 0
        self.traits = []

class Player:
    def __init__(self, mytype):
        self.type = mytype
        self.name = "anonymous"
        self.health = 3

        self.x = -1
        self.y = -1
        self.side = -1
        self.action = Action.Start
        self.done = False
        self.moved = 0
        self.posture = Posture.Standing


class Messages:
    def __init__(self):
        self.msgs = []
        self.wrap = textwrap.TextWrapper(width=30,subsequent_indent="  ")
    def get(self,idx):
        if idx < 0 or idx >= len(self.msgs):
            return ''
        return self.msgs[len(self.msgs)-1-idx]
    def add(self,msg):
        ml = self.wrap.wrap(msg)
        for l in ml:
            self.msgs.append(l)


def d6(count = 1):
    total = 0
    while count > 0:
        total += random.randint(1,6)
        count -= 1
    return total

def randomBoard(board):
    for y in range(0,Board.HEIGHT):
        for x in range(0,Board.WIDTH//2):
            tl = (Tile.Ground,Tile.Ground,Tile.Ground,Tile.Wall,Tile.Wall,
                  Tile.Ground,Tile.Ground,Tile.Ground,
                  Tile.Ground,Tile.Ground,Tile.Ground,Tile.Ground,Tile.Ground,
                  Tile.Door, Tile.Window, Tile.Brambles,
                  Tile.Water, Tile.Tree)
            tt = random.choice(tl)
            board.board[board.coord(x,y)] = tt
            board.board[board.coord(Board.WIDTH-x-1,y)] = tt

class Board:
    WIDTH = 24
    HEIGHT = 24
    def __init__(self):
        self.turnno = 1    # current turn number
        self.turn = 0      # player number whose turn it is
        self.board = [Tile.Ground] * (Board.WIDTH * Board.HEIGHT)
        self.players = []
        self.types = {}

        self.flag1x = 2
        self.flag1y = 8
        self.flag1  = None
        self.flag2x = 28
        self.flag2y = 8
        self.flag2  = None

        self.log = Messages()

    def addType(self, type):
        self.types[type.ident] = type
    def getType(self, ident):
        if ident in self.types:
            return self.types[ident]
        return None

    def endTurn(self):
        if self.turn == 0:
            self.turn = 1
        else:
            self.turn = 0
            self.turnno += 1
        for p in self.players:
            p.action = Action.Start
            p.done = False
            p.moved  = 0

    def valid(self, x, y):
        if x < 0 or y < 0:
            return False
        if x >= Board.WIDTH or y >= Board.HEIGHT:
            return False
        return True
    def coord(self, x, y):
        if not self.valid(x,y):
            return None
        return x + y * Board.WIDTH
    def shift(self, x, y, dir):
        if dir == Direction.North:
            y -= 1
        elif dir == Direction.East:
            x += 1
        elif dir == Direction.South:
            y += 1
        elif dir == Direction.West:
            x -= 1
        elif dir == Direction.Northwest:
            x -= 1
            y -= 1
        elif dir == Direction.Northeast:
            x += 1
            y -= 1
        elif dir == Direction.Southeast:
            x += 1
            y += 1
        elif dir == Direction.Southwest:
            x -= 1
            y += 1
        return x, y

    def unitCount(self, forSide = -1):
        total = 0
        for unit in self.players:
            if forSide == -1 or unit.side == forSide:
                total += 1
        return total
    def unitsUnmoved(self, forSide):
        total = 0
        for unit in self.players:
            if unit.side == forSide and unit.action == Action.Start:
                total += 1
        return total

    def playerAt(self, x, y):
        for ply in self.players:
            if ply.x == x and ply.y == y:
                return ply
        return None
    def at(self, x, y):
        pos = self.coord(x,y)
        if pos == None:
            return "?"
        return self.board[pos]
    def isOpen(self, x, y):
        if not self.valid(x,y):
            return False
        if self.at(x,y) in (Tile.Wall, Tile.Window, Tile.Tree):
            return False
        if self.playerAt(x,y) != None:
            return False
        return True
    def isAdjacent(self, x, y, notside):
        for dy in range(-1,2):
            for dx in range(-1,2):
                unit = self.playerAt(x+dx,y+dy)
                if unit != None and unit.side != notside:
                    return True
        return False

    def tryAttack(self, actor, dir):
        x, y = self.shift(actor.x, actor.y, dir)
        target = self.playerAt(x,y)

        # make sure there's someone in the target space and that they're not
        # on the same side
        if target == None or target.side == actor.side:
            return Result.Cant

        # start the log message
        msg = []
        bonus = []
        roll = d6()
        bonus.append("{}: Base Roll. ".format(roll))
        bonus.append("+{}: Attacker's Combat. ".format(actor.type.combat))
        bonus.append("-{}: Defender's Evade. ".format(target.type.evade))
        roll += actor.type.combat
        roll -= target.type.evade
        self.log.add("Combat attack: need 4+, got {}.".format(roll))
        for line in bonus:
            self.log.add(line)

        # determine the result
        actor.action = Action.Attack
        if roll <= 1:
            self.log.add("Fumbled attack.")
            self.doDamage(actor, target.strength - actor.defense)
        if roll <= 3:
            self.log.add("Attack failed.")
        else:
            self.doDamage(actor, actor.strength - target.defense)

        self.log.add(''.join(msg))
        return Result.Bad
    def doDamage(self, target, amount):
        if amount < 1:
            amount = 1
        target.health -= amount
        self.log.add("{} took {} damage.".format(target.name, amount))
        pass

    def tryMove(self, actor, dir):
        x, y = self.shift(actor.x, actor.y, dir)
        cost = 1

        # check to see if we can even go in the specified direction
        if not self.isOpen(x,y):
            return Result.Cant
        # check to make sure we're not out of movement
        if actor.moved >= actor.type.move:
            return Result.Cant

        oldX = actor.x
        oldY = actor.y
        oldTile = self.at(actor.x, actor.y)
        # more expensive to move out of water
        if oldTile == Tile.Water:
            cost += 1
        # more expensive to move if adjacent
        if self.isAdjacent(oldX, oldY, actor.side):
            cost += 1
        # more expensive to stand up first
        if actor.posture == Posture.Prone:
            cost += 1
            actor.posture = Posture.Standing
        # update unit
        actor.moved += cost
        actor.x = x
        actor.y = y
        actor.action = Action.Move

        # check if we're adjacent; if we are, make a withdrawl roll
        if self.isAdjacent(oldX, oldY, actor.side):
            msg = []
            roll = d6()
            result = roll

            msg.append("Withdrawal: need 4+, got ")
            if self.isAdjacent(x,y,actor.side):
                result -= 1
                msg.append(str(result))
                msg.append(" (rolled ")
                msg.append(str(roll))
                msg.append(", -1 for entering adjacency")
                msg.append(")")
            else:
                msg.append(str(roll))
            self.log.add("".join(msg))

            if roll <= 3:
                self.log.add("Fell over.")
                actor.posture = Posture.Prone
                actor.done = True
                return Result.Bad

        # if we exited brambles, check for falling over
        if oldTile == Tile.Brambles:
            roll = d6()
            self.log.add("Escape brambles: need 2+, got "+str(roll))
            if roll == 1:
                self.log.add("Fell over.")
                actor.done = True
                actor.posture = Posture.Prone
                return Result.Bad

        if actor.moved >= actor.type.move:
            self.log.add("Out of movement.")
            actor.done = True
            return Result.Bad
        return Result.Good


class Game:
    def __init__(self):
        self.cursX = 0
        self.cursY = 0
        self.selected = None # the currently selected player
        self.mode = Mode.Normal
        self.board = None

    def setupData(self):
        self.board = Board()
        self.dicelog = self.board.log
        t = PlayerType(0,"swordsman")
        self.board.addType(t)
        t = PlayerType(1,"archer")
        self.board.addType(t)

        randomBoard(self.board)
        for i in range(0,20):
            x = -1
            y = -1
            while not self.board.isOpen(x,y):
                x = random.randint(0,Board.WIDTH-1)
                y = random.randint(0,Board.HEIGHT-1)
            p = Player(self.board.getType(i%2))
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
        for y in range(0, Board.HEIGHT):
            for x in range(0, Board.WIDTH):
                display.reset()
                if x == self.cursX and y == self.cursY:
                    display.highlight()
                p = gameBoard.playerAt(x,y)
                if p != None:
                    if p.side == 0:
                        display.color(display.BRIGHTBLUE)
                    else:
                        display.color(display.BRIGHTRED)
                    if p.posture == Posture.Prone:
                        display.mvchar(x*2,y,"p")
                    elif p.action == Action.Move:
                        display.mvchar(x*2,y,"m")
                    else:
                        display.mvchar(x*2,y,str(p.side+1))
                else:
                    tt = gameBoard.at(x,y)
                    if tt == Tile.Ground:
                        display.mvchar(x*2,y,".")
                    elif tt == Tile.Wall:
                        display.mvchar(x*2,y,"#")
                    elif tt == Tile.Tree:
                        display.mvchar(x*2,y,"T")
                    elif tt == Tile.Door:
                        display.mvchar(x*2,y,"+")
                    elif tt == Tile.Water:
                        display.mvchar(x*2,y,"~")
                    elif tt == Tile.Brambles:
                        display.mvchar(x*2,y,"^")
                    elif tt == Tile.Window:
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
            if phere.posture == Posture.Prone:
                pname.append(") - Prone")
            elif phere.action == Action.Start:
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
            return Direction.East
        if key == display.DOWN or key == ord("x"):
            return Direction.South
        if key == display.LEFT or key == ord("a"):
            return Direction.West
        if key == display.UP or key == ord("w"):
            return Direction.North
        if key == key == ord("q"):
            return Direction.Northwest
        if key == key == ord("e"):
            return Direction.Northeast
        if key == key == ord("c"):
            return Direction.Southeast
        if key == key == ord("z"):
            return Direction.Southwest
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
                        if selected.side == self.board.turn and selected.action == Action.Start:
                            self.mode = Mode.Move
                            self.dicelog.add("Moving " + selected.name + "...")
                elif key == ord("t"):
                    selected = b.playerAt(self.cursX, self.cursY)
                    if selected != None:
                        if selected.side == self.board.turn and selected.action == Action.Start:
                            self.mode = Mode.Melee
                            self.dicelog.add(selected.name + "initiating melee attack...")


            elif self.mode == Mode.EndTurn:
                if key == 10:
                    self.board.endTurn()
                self.mode = Mode.Normal

            elif self.mode == Mode.Move:
                dir = self.keyToDir(key)
                if dir != None:
                    if b.tryMove(selected, dir) == Result.Bad:
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
                        if b.tryAttack(selected, dir) != Result.Cant:
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
