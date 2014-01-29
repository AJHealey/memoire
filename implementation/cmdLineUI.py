import sys
import threading
import time
import curses

class cmdLineGUI:

    def __init__(self, controller):
        self.controller = controller
        self.frequence = 24 #hertz
        
        self.running = True

        self.statusLock = threading.Lock()
        self.statusTouched = False
        self.status = ''
        self.setStatus('ok') 
        
        self.eventsLock = threading.Semaphore()
        self.eventsTouched = False
        self.events = []

        self.maxEvent = 10

        # GUI thread
        self.uiThread = threading.Thread(target=curses.wrapper, args=(cmdLineGUI.mainLoop, self))
        self.uiThread.start()



    def addEvent(self, event):
        '''Add an event in a thread safe way'''
        with self.eventsLock:
            if len(self.events) > self.maxEvent -1:
                self.events = self.events[-(self.maxEvent-1):] + [event]
            else:
                self.events = self.events + [event]
            self.eventsTouched = True

    def getEvents(self):
        '''get the events list in a thread safe way'''
        with self.eventsLock:
            tmp = self.events
            self.eventsTouched = False

        return tmp


    def setStatus(self, status):
        '''set the status in a thread safe way'''
        self.statusLock.acquire()
        self.status = "wO " + " ".join(status.split('\n'))
        self.statusTouched = True
        self.statusLock.release()

    def getStatus(self):
        '''get the status in a thread safe way'''
        self.statusLock.acquire()
        tmp = self.status
        self.statusTouched = False
        self.statusLock.release()
        return tmp


    def exceptionInController(self, exception):
        self.setStatus('controller error: ' + exception.args)

    def exit(self):
        self.running = False
        self.controller.exit()

    def mainLoop(stdscr, self):

        statusWin = stdscr.subwin(3, curses.COLS, 0, 0)
        yStat, xStat = statusWin.getmaxyx()
        eventWin = stdscr.subwin(self.maxEvent, 50, 3, 0)
        eventWin.border()
        yEvent, xEvent = eventWin.getmaxyx()

        stdscr.clear()
        stdscr.nodelay(1)
        cmd = ''

        while(self.running):
            # Status update
            if self.statusTouched:
                statusWin.clear()
                statusWin.addnstr(1, 0, self.getStatus(), xStat)
                statusWin.refresh()

            # Events update
            if self.eventsTouched:
                eventWin.clear()
                for i,e in enumerate(self.getEvents()):
                    eventWin.addnstr(i,0, e, xEvent)
                eventWin.refresh()

            # Prompt
            stdscr.addstr(curses.LINES-1,0,"[->]: ")
            stdscr.clrtoeol()
            stdscr.addnstr(cmd, curses.COLS-10)
            stdscr.refresh()

            # Input
            c = stdscr.getch()
            if c != -1:
                if c == ord('\n'):
                    self.controller.newCmd(cmd)
                    cmd = ''
                elif c == ord('\x7f'):
                    cmd = cmd[:-1]
                else:
                    cmd += chr(c)
            if cmd == 'exit':
                self.exit()
                break
            time.sleep(1/self.frequence)




    

 



