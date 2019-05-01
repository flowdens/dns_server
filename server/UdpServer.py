import socket
import select
import multiprocessing as mp


class Server:
    DNS_PORT = 53
    IP = '127.0.0.1'
    MAX_DGRAM_LENGTH = 512
    FORWARDER = '8.8.8.8'

    def __init__(self, action):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((self.IP, self.DNS_PORT))
        self.sock.setblocking(False)
        self.action = action
        self.buffer = []

    def run(self):
        print("Listening...")
        while True:
            socket_list = [self.sock]
            read_sockets, _, _ = select.select(socket_list, [], [], 2)
            for sock in read_sockets:
                if sock == self.sock:
                    data, addr = self.sock.recvfrom(self.MAX_DGRAM_LENGTH)
                    if not data:
                        print('Disconnected from server')
                        continue
                    else:
                        result = self.action(data)

                        if result is None:
                            continue
                        self.sock.sendto(result, addr)

    def stop(self):
        self.sock.close()
