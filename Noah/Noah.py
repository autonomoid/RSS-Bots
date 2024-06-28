#!/usr/bin/env python

### Noah the bot launcher ###

import socket
import sys
import string
import random

class bot:

    def __init__(self):
        pass

    def connect(self, server, port, channel):
        self.server = server
        self.port = port
        self.channel = channel
        self.nick = self.newNick()
        print self.nick
        self.irc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.irc.connect((self.server, self.port))
        data = self.irc.recv(4096)
        print data
        self.irc.send('NICK ' + self.nick + '\r\n')
        self.irc.send('USER ' + self.nick + ' ' + self.nick + ' ' + self.nick + ' :' + self.nick + ' IRC\r\n')
        self.irc.send('JOIN #' + self.channel + '\r\n')

    def parse(self):
        data = self.irc.recv(4096)
        if data:
                if data.split()[0].find('PING') != -1:
                    address = data.split()[1][1:]
                    self.irc.send('PONG :' + str(address) + '\r\n')
                    print 'PINGING SERVER'

                # Join a channel.
                if data.find('BOT_JOIN') != -1:
                    channel = str(''.join(data.split(':')[3:]).rstrip('\r\n'))
                    self.irc.send('JOIN #' + channel + '\r\n')

                # Leave a channel.
                if data.find('BOT_PART') != -1:
                    channel = str(''.join(data.split(':')[3:]).rstrip('\r\n'))
                    self.irc.send('PART #' + channel + '\r\n')

                # Message a channel.
                if data.find('BOT_POST') != -1:
                    channel = str(''.join(data.split(':')[3]).rstrip('\r\n'))
                    msg = str(''.join(data.split(':')[4:]).rstrip('\r\n'))
                    self.irc.send('PRIVMSG #' + str(channel) + ' :' + str(msg) + '\r\n')

    def newNick(self):
        nick = ''
        chars = 'abcdefghijklmnopqrstuvwxyz1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        for x in range(1, 10):
            nick = nick + random.choice(chars)
        return nick

#==========|ENTRY POINT|==========#

if __name__ == '__main__':
    server = sys.argv[1]
    port = int(sys.argv[2])
    channel = sys.argv[3]
    bots = []

    for n in range(0, int(sys.argv[4])):
        bots.append(bot())
        bots[n].connect(server, port, channel)
        print 'Bot ' + str(n) + ' connected.'

    while(True):
        for bot in bots:
            bot.parse()
