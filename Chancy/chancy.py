#!/usr/bin/env python

### Chancy the (channel) utility bot

    #=====================================================================
    # Name: chancy
    #
    # Description: Simple python IRC bot.
    # Author: Autonomoid (2012)
    #
    # Licence:
    #
    #   This program is free software: you can redistribute it and/or
    #   modify it under the terms of the GNU General Public License as
    #   published by the Free Software Foundation, either version 3 of
    #   the License, or (at your option) any later version.
    #
    #   This program is distributed in the hope that it will be useful,
    #   but WITHOUT ANY WARRANTY; without even the implied warranty of
    #   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    #   GNU General Public License for more details.
    #
    #   You should have received a copy of the GNU General Public License
    #   along with this program.
    #=====================================================================

import socket
import time

# Basic user, server and channel settings
nick = 'chancy'
server = 'irc.server.net'
port = 6667
chan = '#channel'

# The bot can grant the following users op status:
op_passwds = {
                'OP_NICK_1': 'pa55w0rd1',
                'OP_NICK_2': 'pa55w0rd2'
             }

online_ops = []

kick_counter = {}


def Help(callerID):
    output = [
              "Hello, I'm " + nick + ". I will respond to the following commands:",
              "    help -> tell you what I'm currently telling you (I guess you figured that already :p).",
              "    author -> tell you my creator's name.",
              "    datetime -> tell you what the local date and time are.",
              "    op <password> -> I shall grant thee op status."
             ]

    if callerID in online_ops:
        op_output = [
                    "",
                    "OP COMMANDS",
                    "    kick_counter -> show who's been messing about :)",
                    ]

        output += op_output

    for line in output:
        irc.send('PRIVMSG ' + callerID + ' :' + line + '\r\n')
        print 'Outgoing = ' + line


def kick_count(callID):

    if callID not in kick_counter:
        kick_counter[callerID] = 0

    kick_counter[callerID] += 1
    irc.send('PRIVMSG ' + callerID + ' :Strike ' + str(kick_counter[callerID]) + '\r\n')
    print 'Outgoing = PRIVMSG ' + callerID + ' :Strike ' + str(kick_counter[callerID]) + '\r\n'

    # 3 strikes and you're out!
    if kick_counter[callerID] > 2:
        irc.send('KICK ' + chan + ' ' + callerID + '\r\n')
        print 'Outgoing = KICK ' + chan + ' ' + callerID + '\r\n'

        irc.send('PRIVMSG ' + callerID + ' :Kick!\r\n')
        print 'PRIVMSG ' + callerID + ' :Kick!.\r\n'


def MakeOP(callerID):
    # Has the user been kicked from the channel?
    if kick_counter[callerID] < 3:

        # Is the user on the list of authorized ops?
        if callerID in op_passwds:

            # Did the user supply a password?
            if len(cmd.split()) > 1:

                # Was it the right password?
                if cmd.split()[1].rstrip('\r\n') == op_passwds[callerID]:
                    irc.send('MODE ' + chan + ' +o ' + callerID + '\r\n')
                    print 'Outgoing = MODE +o ' + callerID + '\r\n'

                    irc.send('PRIVMSG ' + callerID + ' :With great power comes great responsibility.\r\n')
                    print 'PRIVMSG ' + callerID + ' :With great power comes great responsibility.\r\n'

                    online_ops.append(callerID)

                else:
                    irc.send('PRIVMSG ' + callerID + ' :That is not your password ' + callerID + '.\r\n')
                    print 'Outgoing = PRIVMSG ' + callerID + ' :That is not your password ' + callerID + '.\r\n'
                    kick_count(callerID)
            else:
                irc.send('PRIVMSG ' + callerID + ' :Looks like you forgot to enter a password ' + callerID + '.\r\n')
                print 'Outgoing = PRIVMSG ' + callerID + ' :Looks like you forgot to enter a password ' + callerID + '.\r\n'
        else:
            irc.send('PRIVMSG ' + callerID + ' :Your nick is not on my list of authorized ops ' + callerID + '.\r\n')
            print 'Outgoing = PRIVMSG ' + callerID + ' :Your nick is not on my list of authorzed ops ' + callerID + '.\r\n'
    else:
        irc.send('PRIVMSG ' + callerID + ' :You have been kicked from ' + chan + '.\r\n')
        print 'Outgoing = PRIVMSG ' + callerID + ' :You have been kicked from ' + chan + '.\r\n'

# Setup a socket and connect tot he server.
irc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
irc.connect((server, port))

# Setup a 4096B buffer.
irc.recv(4096)

# Send my nick to the server.
irc.send('NICK ' + nick + '\r\n')

# Send my user info to the server.
irc.send('USER ' + nick + ' ' + nick + ' ' + nick + ' :' + nick + ' IRC\r\n')

# Join the channel.
irc.send('JOIN ' + chan + '\r\n')

# While still connected:
while True:

    # Fetch data from the irc socket.
    data = irc.recv(4096)

    # Print the data a line at a time.
    for line in data.split('\n'):
        print 'Incoming = ' + line

    # Did you get a ping?.
    if data.find('PING') != -1:
        # Was it from the IRC server?
        if server.replace('irc.', '') in data:
            irc.send('PONG ' + data.split()[1] + '\r\n')

    # Did someone join?
    if data.find('JOIN ' + chan) != -1 and data.find(nick) == -1:

        # Find out who joined and say hello.
        newguy = data.split('!')[0][1:]
        irc.send('PRIVMSG ' + chan + ' :Hi ' + newguy + ', welcome to ' + chan + '\r\n')
        print 'Outgoing = PRIVMSG ' + chan + ' :Hi ' + newguy + ', welcome to ' + chan + '.\r\n'

        # Init their kick-counter
        kick_counter[newguy] = 0
        print 'kick_counter:'
        print kick_counter

    # Did someone leave?
    if data.find('PART ' + chan) != -1 and data.find(nick) == -1:

        # Find out who left.
        quitter = data.split('!')[0][1:]

        # If they were an op remove them from online_ops.
        if quitter in online_ops:
            online_ops.remove(quitter)

    # Were we sent a PM?
    if data.find('PRIVMSG ' + nick) != -1:

        # Grab the current command.
        cmd = ''.join(data.split(':')[2:]).rstrip('\r\n')

        # Find out who issued the command.
        callerID = data.split('!')[0][1:]

        # Make sure everyone is registered in the kick list.
        if callerID not in kick_counter:
            kick_counter[callerID] = 0

        ################# COMMANDS ############################

        # Help
        if cmd == 'help':
            Help(callerID)

        # Print author's details
        if cmd == 'author':
            irc.send('PRIVMSG ' + callerID + ' :Coded by AUTHOR\r\n')
            print 'Outgoing = PRIVMSG ' + callerID + ' :Coded by AUTHOR\r\n'

        # Print the date and time
        if cmd == 'datetime':
            datetime = time.asctime(time.localtime(time.time()))
            irc.send('PRIVMSG ' + callerID + ' :' + str(datetime) + '\r\n')
            print 'Outgoing = ' + str(datetime)

        # Make user an OP
        if cmd.split()[0] == 'op':
            MakeOP(callerID)

        ##################### OP TOOLS #########################
        if callerID in online_ops:

            # Show kick_counter
            if cmd == 'kick_counter':
                irc.send('PRIVMSG ' + callerID + ' :kick_counter\r\n')
                print 'Outgoing = PRIVMSG ' + callerID + ' :kick_counter\r\n'
                for kickee in kick_counter:
                    irc.send('PRIVMSG ' + callerID + ' :    NICK = ' + kickee + ', STRIKES = ' + str(kick_counter[kickee]) + '\r\n')
                    print 'Outgoing = PRIVMSG ' + callerID + ' :    NICK = ' + kickee + ', STRIKES = ' + str(kick_counter[kickee]) + '\r\n'
