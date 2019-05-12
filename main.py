import sys
from server.DnsCacheManager import DnsServer

if __name__ == '__main__':
    server = DnsServer()
    try:
        server.run()
    except KeyboardInterrupt:
        print('Server shutdown')
    finally:
        print("Caching process")
        server.cache.save_records()
        server.stop()
        sys.exit(0)
