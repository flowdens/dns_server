import sys
from server.UdpServer import Server


if __name__ == '__main__':
    server = Server(print)

    try:
        server.run()
    except KeyboardInterrupt:
        print("Caching")
        print('Server shutdown')
        # save cache
        server.stop()
        sys.exit(0)
