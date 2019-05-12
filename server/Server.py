import socket
import selectors


class CallbackData:
    def __init__(self, callback, *args, **kwargs):
        self.callback = callback
        self.args = args
        self.kwargs = kwargs


class Server:
    DNS_PORT = 53
    LOCALHOST = '127.0.0.1'
    MAX_DGRAM_LENGTH = 512

    def __init__(self, action):
        self.server_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server_sock.bind((self.LOCALHOST, self.DNS_PORT))
        self.server_sock.setblocking(False)
        self.selectors = selectors.DefaultSelector()
        self.selectors.register(self.server_sock, selectors.EVENT_READ, data=CallbackData(self.read))
        self.action = action

    def read(self):
        data, addr = self.server_sock.recvfrom(self.MAX_DGRAM_LENGTH)
        print(f"Accepted from {addr[0]} : {addr[1]}")
        # print(data)
        if not data:
            print('Disconnected from server')
            return
        self.action(data, addr)

    def run(self):
        print("Listening...")
        while True:
            events = self.selectors.select(timeout=2)
            for key, _ in events:
                data = key.data
                data.callback(*data.args, **data.kwargs)

    def stop(self):
        self.server_sock.close()
