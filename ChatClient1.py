import FactoryChat
import time
import pickle
from socket import socket
from threading import Thread
from FactoryChat import User, Message, MessageFactory
import os
import sys

IP = "127.0.0.1"
PORT = 9999
READ_LEN = 1024
LEN_OF_LEN = 10
MSG_FACTORY = MessageFactory()
MUTED = False


def get_time():
    """
    Gets the time right now
    :return: time right now as string: HH:MM
    """
    return time.strftime("%H:%M")


def check_name():
    """
    Checking user that connect has not a blank name or starts with @
    :return: name of user
    """
    while True:
        name = raw_input("Enter name: ")
        if name.startswith("@"):
            print "You cannot use @ before your name"
        elif not name:
            print "Name cannot be empty"
        else:
            break
    return name


USER = User(check_name(), False)
FIRST_CONNECTION = "The user {} was connected".format(USER.name)


def full_recv(client_socket, len_read):
    """
    Gets the message from server and transfer it into a regular string
    :return: client message str
    """
    ret_st = ""
    while len(ret_st) < len_read:
        ret_st += client_socket.recv(len_read - len(ret_st))
    return ret_st


def read_from_server_socket_by_protocol(client_socket):
    """
    Get message len and the message itself by the function full_recv
    :return: message
    """
    len_of_msg = int(full_recv(client_socket, LEN_OF_LEN))
    msg = full_recv(client_socket, len_of_msg)
    return msg


def send_thread(client_socket):
    """
    Gets client_socket, waiting for user input and send it to server
    """
    while True:
        client_msg = MSG_FACTORY.factory(raw_input(), USER.name)
        if not MUTED:
            client_msg = pickle.dumps(client_msg)
            client_socket.send(str(len(client_msg)).zfill(LEN_OF_LEN))
            client_socket.send(client_msg)

            client_msg = pickle.loads(client_msg)
            if client_msg.msg_type == FactoryChat.QUIT_COMMAND:
                ans = raw_input("Want to rejoin? Y/N\n")
                if ans == "Y":
                    main()
                    break
                else:
                    os.execl(sys.executable, *([sys.executable] + sys.argv))
        else:
            print "You cannot speak here."


def check_recv(server_msg):
    """
    Checks the server message type and print as need
    """
    if isinstance(server_msg, Message):
        print "{} {}: {}".format(get_time(), server_msg.user, server_msg.msg)
    elif server_msg is None:
        pass
    elif server_msg.endswith("was promoted to be manager"):
        server_msg_cut = server_msg.split()
        if server_msg_cut[1] == "@" + USER.name:
            USER.name = server_msg_cut[1]
            USER.manager = True
        print server_msg
    elif server_msg.startswith("You cannot speak here, "):
        server_msg_cut = server_msg.split("You cannot speak here, ")
        if server_msg_cut[1] == USER.name:
            global MUTED
            MUTED = True
            print "You cannot speak here."
    elif "!" in server_msg:
        server_msg_cut = server_msg.split(" ", 1)
        if server_msg_cut[0] == USER.name:
            print server_msg_cut[1]
    else:
        print server_msg


def recv_thread(client_socket):
    """
    Gets client_socket, receives message from server and print it on screen
    """
    while True:
        server_msg = read_from_server_socket_by_protocol(client_socket)
        server_msg = pickle.loads(server_msg)
        check_recv(server_msg)


def main():
    """
    Main function of the program
    """
    client_socket = socket()
    client_socket.connect((IP, PORT))

    client_socket.send(str(len(pickle.dumps(USER))).zfill(LEN_OF_LEN))
    client_socket.send(pickle.dumps(USER))

    client_socket.send(str(len(pickle.dumps(FIRST_CONNECTION))).zfill(LEN_OF_LEN))
    client_socket.send(pickle.dumps(FIRST_CONNECTION))
    print """Connected to group chat.
        COMMANDS:
         ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        | quit                          | Leave chat                                |
         ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
         ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        | kick <user> (admin only)      | Kick someone from the chat (except admin) |
         ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
         ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        | inviteMan <user> (admin only) | Promote user to be manager                |
         ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
         ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        | mute <user> (admin only)      | Mute user (except admin)                  |
         ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
         ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        | !<user> <message>             | Private message user                      |
         ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
         ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        | view-managers                 | View admin list                           |
         ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        """

    # creating 2 threads, one for receiving data and one for sending data
    t1 = Thread(target=recv_thread, args=[client_socket])
    t1.start()
    t2 = Thread(target=send_thread, args=[client_socket])
    t2.start()


if __name__ == '__main__':
    main()
