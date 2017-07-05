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

        self.x = -1
        self.y = -1
        self.side = -1
        self.action = Action.Start
        self.done = False
        self.moved = 0
        self.health = self.type.health
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
            self.doDamage(actor, actor.type.strength - target.type.defense)

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
