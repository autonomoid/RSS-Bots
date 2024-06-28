#!/usr/bin/env python

### LIRC the log bot ###

import socket
import time
import logging

# Font effects
underline = "\x1b[1;4m"
black = "\x1b[1;30m"
red = "\x1b[1;31m"
green = "\x1b[1;32m"
yellow = "\x1b[1;33m"
blue = "\x1b[1;34m"
purple = "\x1b[1;35m"
turquoise = "\x1b[1;36m"
normal = "\x1b[0m"

FLAG_CONNECTED = False
irc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
data = ''
log = logging.getLogger()

users = {
         'AlanT': {
                   'times': {
                             'last_join': 0.0,
                             'last_part': 0.0,
                             'last_pm': 0.0,
                             'last_chat': 0.0
                            },
                   'counters': {
                                'total_pms': 0,
                                'total_chats': 0
                               },
                   'verified_human': False,
                   'bot_factor': 100
                  }
        }


def initLog():
    """Initialize the logger"""
    log.setLevel(logging.DEBUG)
    f = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s",
                          "%Y-%m-%d %H:%m:%S")
    h = logging.StreamHandler()
    h.setFormatter(f)
    h.setLevel(logging.DEBUG)
    log.addHandler(h)


def connect():
    irc.connect((server, port))
    irc.recv(4096)
    irc.send('NICK ' + nick + '\r\n')
    irc.send('USER ' + nick + ' ' + nick + ' ' + nick + ' :' + nick + ' IRC\r\n')
    irc.send('JOIN ' + chan + '\r\n')


def parse():
    data = irc.recv(4096)

    # Print the data a line at a time.
    if data:
        t = time.time()
        for line in data.split('\n'):
            log.debug(blue + str(line) + normal)

        # ping?.
        if data.split()[0].find('PING') != -1:
            event_ping(data, t)

        # connected?
        global FLAG_CONNECTED
        if FLAG_CONNECTED == False:
            if data.find(nick + ' ' + chan + ' :End of /NAMES list.') != -1:
                event_connected(t)

        # chat?
        if data.find('PRIVMSG ' + chan) != -1:
            event_chat(data, t)

        # join?
        if data.find('JOIN ' + chan) != -1 and data.find(nick) == -1:
            event_join(data, t)

        # part?
        if data.find('PART ' + chan) != -1 and data.find(nick) == -1:
            event_part(data, t)

        # pm?
        if data.find('PRIVMSG ' + nick) != -1:
            event_pm(data, t)

#==========|ACTIONS|==========#


def action_ban(nick):
    log.info('action_ban()')


def action_kick(nick):
    log.info('action_kick()')


def action_chat(msg):
    log.debug(blue + 'action_chat()' + normal)
    irc.send('PRIVMSG ' + str(chan) + ' :' + str(msg) + '\r\n')
    log.info('PRIVMSG ' + str(chan) + ' :' + str(msg) + '.\r\n')


def action_pm(nick, msg):
    log.info('action_pm()')


def action_pong(address):
    log.debug(blue + 'action_pong(' + str(address) + ')' + normal)
    irc.send('PONG :' + str(address) + '\r\n')


def action_ignore(nick):
    log.info('action_ignore()')


def action_getusers(chan, t):
    log.debug(blue + 'action_getusers(' + str(t) + ')' + normal)
    irc.send('NAMES ' + str(chan) + '\r\n')
    while True:
        data = irc.recv(4096)
        global nick
        if data.find(nick + ' ' + chan + ' :End of /NAMES list.') != -1:
            break

        # Check that two ':' are present. If not it could be a flood warning.
        if len(data.split(':')) < 3:
            log.info('Possible flood warning detected!')
            break
        nicks = data.split(':')[2].split()
        for n in nicks:
            if n not in users:
                action_adduser(n, t)


def action_adduser(nick, t):
    log.debug(blue + 'action_adduser(' + str(nick) + ', ' + str(t) +
              ')' + normal)
    users[nick] = {
                    'times': {
                              'last_join': t,
                              'last_part': t,
                              'last_pm': t,
                              'last_chat': t
                             },
                    'counters': {
                                 'total_pms': 0,
                                 'total_chats': 0
                                },
                    'verified_human': False,
                    'bot_factor': 0
                  }


def action_save():
    log.debug(blue + 'action_save()' + normal)
    f = open('data.csv', 'w')
    f.write('user,last_join,last_part,last_pm,last_chat,total_pms,' +
            'total_chats,verfied_human,bot_factor,time\n')
    for u in users:
        t = str(time.time())
        last_join = str(users[u]['times']['last_join'])
        last_part = str(users[u]['times']['last_part'])
        last_pm = str(users[u]['times']['last_pm'])
        last_chat = str(users[u]['times']['last_chat'])
        total_pms = str(users[u]['counters']['total_pms'])
        total_chats = str(users[u]['counters']['total_chats'])
        verified_human = str(users[u]['verified_human'])
        bot_factor = str(users[u]['bot_factor'])
        output = (u + ',' + last_join + ',' + last_part + ',' + last_pm + ',' +
                  last_chat + ',' + total_pms + ',' + total_chats + ',' +
                  verified_human + ',' + bot_factor + ',' + t + '\n')
        f.write(output)
    f.close()


def action_logchat(nick, msg):
    log.debug(blue + 'action_logchat(' + str(nick) + ', msg)' + normal)
    f = open('logs/' + nick + '.log', 'a')
    f.write(msg + '\n\n')
    f.close()

#==========|EVENTS|==========#


def event_connected(t):
    log.debug(blue + 'event_connected(' + str(t) + ')' + normal)
    action_getusers(chan, t)
    global FLAG_CONNECTED
    FLAG_CONNECTED = True


def event_ping(data, t):
    address = data.split()[1][1:]
    log.debug(blue + 'event_ping(' + str(address) + ')' + normal)
    action_pong(address)


def event_chat(data, t):
    sender = data.split('!')[0][1:]
    if sender not in users:
        action_adduser(sender, t)
    msg = str(''.join(data.split(':')[2:]).rstrip('\r\n'))
    log.debug(blue + 'event_chat(' + str(sender) + ')' + normal)
    log.info(red + str(sender) + normal + ': ' + yellow + msg + normal)

    previous_time = users[sender]['times']['last_chat']
    users[sender]['times']['last_chat'] = t
    users[sender]['counters']['total_chats'] += 1
    time_diff = t - previous_time

    log.debug(blue + '* delta = ' + str(time_diff) + normal)
    n = users[sender]['counters']['total_chats']
    log.debug(blue + '* total_chats = ' + str(n) + normal)

    action_save()
    action_logchat(sender, msg)


def event_join(data, t):
    newguy = data.split('!')[0][1:]
    log.debug(blue + 'event_join(' + str(newguy) + ')' + normal)
    action_adduser(newguy, t)
    action_save()


def event_part(data, t):
    quitter = data.split('!')[0][1:]
    if quitter not in users:
        action_adduser(quitter, t)
    log.debug(blue + 'event_part(' + str(quitter) + ')' + normal)
    action_save()


def event_pm(data, t):
    sender = data.split('!')[0][1:]
    if sender not in users:
        action_adduser(sender, t)
    log.info('event_pm(' + red + str(sender) + ')' + normal)
    log.info('* msg = ' + yellow + str(data.split(':')[2].rstrip('\r\n'))
             + normal)

    previous_time = users[sender]['times']['last_pm']
    users[sender]['times']['last_pm'] = t
    users[sender]['counters']['total_pms'] += 1
    time_diff = t - previous_time

    log.debug(blue + '* delta = ' + str(time_diff) + normal)
    n = users[sender]['counters']['total_pms']
    log.debug(blue + '* total_pms = ' + str(n) + normal)
    action_save()

#==========|ENTRY POINT|==========#

if __name__ == '__main__':
    nick = raw_input('nick: ')
    server = raw_input('server: ')
    port = int(raw_input('port: '))
    chan = raw_input('chan: ')
    FLAG_CONNECTED = False
    initLog()
    connect()
    while True:
        parse()
