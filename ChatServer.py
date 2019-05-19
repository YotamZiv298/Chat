import FactoryChat
import pickle
import time
from socket import socket
from select import select
from FactoryChat import Message, User

IP = "0.0.0.0"
PORT = 9999
LEN_OF_LEN = 10


def get_time():
    """
    Gets the time right now
    :return: time right now as string: HH:MM
    """
    return time.strftime("%H:%M")


def full_recv(client_socket, len_read):
    """
    Gets the message from client and transfer it into a regular string
    :return: client message str
    """
    ret_st = ""
    while len(ret_st) < len_read:
        ret_st += client_socket.recv(len_read - len(ret_st))
    return ret_st


def read_from_client_socket_by_protocol(client_socket):
    """
    Get message len and the message itself by the function full_recv
    :return: message
    """
    len_of_msg = int(full_recv(client_socket, LEN_OF_LEN))
    msg = full_recv(client_socket, len_of_msg)
    return msg


def check_command(client_msg, clients, ready_socket, users_names, managers_names):
    """
    Checks the command from user/admin
    :return: each state cause different action or string being returned
    """
    if isinstance(client_msg, Message):
        if client_msg.msg_type == FactoryChat.SIMPLE_MESSAGE_COMMAND:
            return client_msg
        elif client_msg.msg_type == FactoryChat.QUIT_COMMAND:
            clients.remove(ready_socket)
            if client_msg.user.startswith("@"):
                managers_names.remove(client_msg.user)
            users_names.remove(client_msg.user)
            return "{} {} has left the chat".format(get_time(), client_msg.user)
        elif client_msg.msg_type == FactoryChat.KICK_COMMAND:
            if client_msg.msg in users_names and not client_msg.msg.startswith("@") and client_msg.user.startswith("@"):
                del clients[users_names.index(client_msg.msg)]
                users_names.remove(client_msg.msg)
                return "{} {} was kicked from the chat".format(get_time(), client_msg.msg)
            return None
        elif client_msg.msg_type == FactoryChat.INVITE_ADMIN_COMMAND:
            if client_msg.user.startswith("@") and not client_msg.msg.startswith("@"):
                for i in range(len(users_names)):
                    if users_names[i] == client_msg.msg:
                        users_names[i] = "@" + client_msg.msg
                        managers_names.append(users_names[i])
                        return "{} {} was promoted to be manager".format(get_time(), users_names[i])
            return None
        elif client_msg.msg_type == FactoryChat.MUTE_COMMAND:
            if client_msg.user.startswith("@") and not client_msg.msg.startswith("@"):
                for i in range(len(users_names)):
                    if users_names[i] == client_msg.msg:
                        return "You cannot speak here, {}".format(users_names[i])
            return None
        elif client_msg.msg_type == FactoryChat.PRIVATE_MESSAGE_COMMAND:
            client_msg.msg = client_msg.msg.split(" ", 1)
            if client_msg.msg[0] in users_names:
                for i in range(len(users_names)):
                    if users_names[i] == client_msg.msg[0]:
                        return "{} {} !{}: {}".format(client_msg.msg[0], get_time(), client_msg.user, client_msg.msg[1])
            return None
        elif client_msg.msg_type == FactoryChat.SEE_ADMINS_COMMAND:
            return "Managers: {}".format(managers_names)
    elif isinstance(client_msg, User):
        if client_msg.name.startswith("@"):
            managers_names.append(client_msg.name)
        users_names.append(client_msg.name)
        return None
    else:
        return client_msg


def handle_clients(clients, users_names, managers_names, server_socket):
    """
    Handles the clients by checking their availability and calling func that check their command/msg and sending back
    response
    :param clients: list of clients that connected to the server
    :param users_names: list of names of the clients
    :param managers_names: list of names of the managers from the clients
    :param server_socket: server socket
    """
    rlist, wlist, xlist = select(clients + [server_socket], [], [])
    for ready_socket in rlist:
        if ready_socket == server_socket:
            client_socket, client_addr = server_socket.accept()
            clients.append(client_socket)
        else:
            try:
                client_msg = read_from_client_socket_by_protocol(ready_socket)

                client_msg = pickle.loads(client_msg)
                client_msg_checked = check_command(client_msg, clients, ready_socket, users_names, managers_names)
                client_msg = pickle.dumps(client_msg_checked)
                if isinstance(client_msg_checked, str) and client_msg_checked.startswith("Managers: "):
                    for client in clients:
                        if client == ready_socket:
                            client.send(str(len(client_msg)).zfill(LEN_OF_LEN))
                            client.send(client_msg)
                            break
                else:
                    for client in clients:
                        if client != ready_socket:
                            client.send(str(len(client_msg)).zfill(LEN_OF_LEN))
                            client.send(client_msg)
            except:
                pass


def initialize_server():
    """
    Creates a server socket and bind it to port
    :returns: initialized server socket
    """
    server_socket = socket()
    server_socket.bind((IP, PORT))
    server_socket.listen(1)
    return server_socket


def main():
    """
    Main function of the program
    """
    server_socket = initialize_server()
    clients = []
    users_names = []
    managers_names = []

    while True:
        time.sleep(0.5)
        handle_clients(clients, users_names, managers_names, server_socket)


if __name__ == '__main__':
    main()
