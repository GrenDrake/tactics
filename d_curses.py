import curses
import logging

logger = None
stdscr = None
LEFT  = curses.KEY_LEFT
RIGHT = curses.KEY_RIGHT
UP    = curses.KEY_UP
DOWN  = curses.KEY_DOWN

BLACK   = 0
RED     = 1
GREEN   = 2
YELLOW  = 3
BLUE    = 4
MAGENTA = 5
CYAN    = 6
GRAY    = 7
BRIGHTRED = 8
BRIGHTGREEN = 9
BRIGHTYELLOW = 10
BRIGHTBLUE = 11
BRIGHTMAGENTA = 12
BRIGHTCYAN = 13
WHITE = 14

def start():
    global logger
    logger = logging.getLogger()
    global stdscr
    stdscr = curses.initscr()
    if curses.has_colors():
        curses.start_color()
        curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        curses.init_pair(4, curses.COLOR_BLUE, curses.COLOR_BLACK)
        curses.init_pair(5, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
        curses.init_pair(6, curses.COLOR_CYAN, curses.COLOR_BLACK)
        curses.init_pair(7, curses.COLOR_WHITE, curses.COLOR_BLACK)
    curses.noecho()
    curses.cbreak()
    stdscr.keypad(True)
    curses.curs_set(0)

def end():
    curses.nocbreak()
    stdscr.keypad(False)
    curses.echo()
    curses.curs_set(1)
    curses.endwin()

def clear():
    stdscr.clear()

def paint():
    stdscr.refresh()

def mvstring(x, y, text):
    stdscr.addstr(y, x, text)

def mvchar(x, y, text):
    logger.debug("mvchar({}, {}, {} -- {}, {}, {})".format(x,y,text, type(x), type(y), type(text)))
    stdscr.addch(y, x, text)

def reset():
    stdscr.attrset(0)

def attr(theColor, theHighlight=False):
    reset()
    color(theColor)
    highlight(theHighlight)

def color(color):
    if curses.has_colors():
        if color > GRAY:
            stdscr.attron(curses.color_pair(color-GRAY))
            stdscr.attron(curses.A_BOLD)
        else:
            stdscr.attron(curses.color_pair(color))

def highlight():
    stdscr.attron(curses.A_REVERSE)

def getkey():
    return stdscr.getch()

