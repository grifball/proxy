#!/usr/bin/python
# This is a simple port-forward / proxy, written using only the default python
# library. If you want to make a suggestion or fix something you can contact-me
# at voorloop_at_gmail.com
# Distributed over MIT license
import socket
import select
import time
import sys
import string

def remove_control_chars(s):
    return ''.join([x for x in s if x in string.printable])

if len(sys.argv)<3:
    print("usage:\n\t"+sys.argv[0]+" <listen port> <remote host>:<remote port>")
    sys.exit(1)

listen_port=None
remote_host=None
remote_port=None
try:
    remote_parts=sys.argv[2].split(':')
    listen_port=int(sys.argv[1])
    remote_host=remote_parts[0]
    remote_port=int(remote_parts[1])
except Exception as e:
    print("An argument was malformed")
    print(e)
    sys.exit(1)

buffer_size = 4096
forward_to = (remote_host, remote_port)

class Forward:
    def __init__(self):
        self.forward = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def start(self, host, port):
        try:
            self.forward.connect((host, port))
            return self.forward
        except Exception as inst:
            print("[exception] - {0}".format(inst.strerror))
            return False    

class TheServer:
    input_list = []
    channel = {}

    def __init__(self, host, port):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((host, port))
        self.server.listen(200)

    def main_loop(self):
        self.input_list.append(self.server)
        while 1:
            ss = select.select
            inputready, outputready, exceptready = ss(self.input_list, [], [])
            for s in inputready:
                if s == self.server:
                    self.on_accept(s)
                    break

                self.data = s.recv(buffer_size)
                if len(self.data) == 0:
                    self.on_close(s)
                    break
                else:
                    self.on_recv(s)

    def on_accept(self, s):
        forward = Forward().start(forward_to[0], forward_to[1])
        clientsock, clientaddr = self.server.accept()
        if forward:
            print("{0} has connected".format(clientaddr))
            self.input_list.append(clientsock)
            self.input_list.append(forward)
            self.channel[clientsock] = forward
            self.channel[forward] = clientsock
        else:
            print("Can't establish a connection with remote server. Closing connection with client side {0}".format(clientaddr))
            clientsock.close()

    def on_close(self, s):
        print("{0} has disconnected".format(s.getpeername()))
        #remove objects from input_list
        self.input_list.remove(s)
        self.input_list.remove(self.channel[s])
        out = self.channel[s]
        # close the connection with client
        self.channel[out].close()  
        # close the connection with remote server
        self.channel[s].close()
        # delete both objects from channel dict
        del self.channel[out]
        del self.channel[s]

    def on_recv(self, s):
        data = self.data
        # here we can parse and/or modify the data before send forward
        print(remove_control_chars(data.decode('utf-8', errors='ignore')))
        self.channel[s].send(data)

if __name__ == '__main__':
        server = TheServer('', listen_port)
        try:
            server.main_loop()
        except KeyboardInterrupt:
            print("Ctrl C - Stopping server")
            sys.exit(1)
