#!/usr/bin/env python

#Copyright (C) 2020  Andreas Winkler

#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.

#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.

#    Version 0.3

import pyinotify
import subprocess
import sys
import os
import logging
import time

from slixmpp import ClientXMPP
from slixmpp.exceptions import IqError, IqTimeout

#---SETTINGS SECTION---

#IMPORTANT
#First create a txt with the same name as the game name (dgame) in the savegame root folder. Example: Test_map.txt
#Write the XMPP name of the players that are supposed to get the notifications, one on each line. Example: 
#David
#Nick
# ...
#Remove a name to stop the notifications to that player

#SERVER
jid = "<id>"
password = "<password>"
xmpp_server = "chat.facebook.com" #Note: Facebook no longer offers XMPP support
xmpp_server_port = "5222"

#Game executable and savegame directories
game_version = "5" #Tested with 4 and 5
game_exec_dir = "/home/<user name>/.steam/steam/steamapps/common/Dominions5/"
savegame_dir = "/home/<user name>/.dominions5/savedgames/"

#GAME
#Host IP (127.0.0.1 for localhost)
dip = "127.0.0.1"

#Game port
dport = "40000"

#Logging (comment to disable)
logging.basicConfig(filename=savegame_dir + "logfile.log",level=logging.DEBUG)

#Game name
dgame = "Test_map"

#Number of players
dplayers = "2"

#Map name
dmap = "silentseas.map"

#Era
dera = "1"

#Hall of Fame size
dhof = "10"

#Independents strength
dind = "5"

#Thrones of Ascension
dtoa = "5 0 0"

#Thrones of Ascension
drtoa = "5"

#---END SETTINGS SECTION---

#START GAME

doptions = " -g " + dgame + " --uploadmaxp " + dplayers + " --mapfile " + dmap + " --era " + dera + " --hofsize " + dhof + " --indepstr " + dind + " --thrones " + dtoa + " --requiredap " + drtoa + " --port " + dport

gameinit =  game_exec_dir + "dom" + game_version + ".sh -S -T --nonationsel --noclientstart" + doptions

subprocess.Popen(gameinit, stdout=subprocess.PIPE, shell=True)

#MESSAGE BOT
class SendMsgBot(ClientXMPP):
    def __init__(self, jid, password, recipient, message):
        ClientXMPP.__init__(self, jid, password)
        self.recipient = recipient
        self.msg = message
        #self.add_event_handler("session_start", self.start, threaded=True)

    def start(self, event):
        for self.pnumber in self.recipient:
            self.send_message(mto=self.pnumber, mbody=self.msg, mtype='chat')
            time.sleep(1)
        self.disconnect(wait=False)

#NEW GAME MESSAGE
if not os.path.isdir(savegame_dir + dgame):

    #Query Game Server
    gamestate = subprocess.Popen(game_exec_dir + "dom" + game_version + ".sh --tcpquery --ipadr " + dip + " --port " + dport, stdout=subprocess.PIPE, shell=True)
    (boutput, error) = gamestate.communicate()

    #Byte to string decoding
    encoding = 'utf-8'
    output = boutput.decode(encoding)

    #Check Game Name

    for cname in output.split(u"\n"):
        if "Gamename" in cname:
            gamename = cname.strip()

    #Check Game Status
    for cstatus in output.split(u"\n"):
        if "Status" in cstatus:
            status = cstatus.strip()

    #If game is waiting for players
    for waiting in output.split(u"\n"):
        if "Waiting" in waiting:
            msg = gamename[10:] + "\n" + "-" + "\n" + "Select Pretenders"

    #Player List
    players = open(savegame_dir + dgame + ".txt", "r")
    to = list(players.readlines())
    players.close()

    #Send Message
    xmpp = SendMsgBot(jid, password, to, msg)

    #FB APP SUPPORT
    #xmpp.credentials['api_key'] = ''
    #xmpp.credentials['access_token'] = ''

    if xmpp.connect(('chat.facebook.com', 5222)):
        xmpp.process(block=True)
    else:
        print("Unable to connect.")

#EVENTHANDLER

wm = pyinotify.WatchManager() # Watch Manager
mask = pyinotify.IN_DELETE | pyinotify.IN_CREATE | pyinotify.IN_CLOSE_WRITE # Watched Events

class EventHandler(pyinotify.ProcessEvent):

    def process_IN_CLOSE_WRITE(self, event):

        suffix = dgame + "/ftherlnd"

        if event.pathname.endswith(suffix):

            #MESSAGE SENDING

            #Query Game Server
            gamestate = subprocess.Popen(game_exec_dir + "dom" + game_version + ".sh --tcpquery" + " --ipadr " + dip + " --port " + dport, stdout=subprocess.PIPE, shell=True)
            (boutput, error) = gamestate.communicate()

                #Byte to string decoding
            encoding = 'utf-8'
            output = boutput.decode(encoding)

            #Check Game Name
            for cname in output.split(u"\n"):
                if "Gamename" in cname:
                    gamename = cname.strip()

            #Check Game Status
            for cstatus in output.split(u"\n"):
                if "Status" in cstatus:
                    status = cstatus.strip()

            #Check Turn Number
            for turn in output.split(u"\n"):
                if "Turn" in turn:
                    msg = gamename[10:] + "\n" + "-" + "\n" + turn.strip()

            #Player List
            players = open(savegame_dir + dgame + ".txt", "r")
            to = list(players.readlines())
            players.close()

            #Send Message
            xmpp = SendMsgBot(jid, password, to, msg)

            #FB APP SUPPORT
            #xmpp.credentials['api_key'] = ''
            #xmpp.credentials['access_token'] = ''

            if xmpp.connect((xmpp_server, xmpp_server_port)):
                xmpp.process(block=True)
            else:
                print("Unable to connect.")

handler = EventHandler()
notifier = pyinotify.Notifier(wm, handler)
wdd = wm.add_watch(savegame_dir, mask, rec=True, auto_add=True)

notifier.loop()