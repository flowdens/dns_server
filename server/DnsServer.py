from records.DnsMesssage import DnsMessage
from records.config import types
import selectors
import socket
from server.Server import Server, CallbackData
from server.Cache import CacheManager


class DnsServer(Server):
    def __init__(self):
        super().__init__(self.handle_packet)
        self.cache = CacheManager().load_records()
        self.forwarder_ip = '212.193.163.6'
        self.forwarder_query_id = 0
        self.FORWARDER_ADDR = (self.forwarder_ip, self.DNS_PORT)
        self.cached_answers_by_query = {}

    def handle_packet(self, bts, addr):
        possible_parse, msg = DnsMessage.try_parse(bts)
        if not possible_parse:
            print("Parsing error")
            return
        # print(f"Handling pocket {msg.header.id}")
        try:
            self._handle_query_message(msg, addr)
        except TypeError:
            print()

    @staticmethod
    def construct_query_from_questions(query_id, questions):
        query = DnsMessage()
        query.header.id = query_id
        query.header.type = 0
        query.header.rec_desired = 1
        query.header.qdcount = len(questions)
        query.questions = questions
        return query

    @staticmethod
    def construct_response_from_answers(client_id, answers):
        response = DnsMessage()
        response.header.id = client_id
        response.header.type = 1
        response.header.ancount = len(answers)
        response.answers = answers
        return response

    def _handle_query_message(self, msg, client_addr):
        answers_to_send, questions_to_lookup = self._get_answers_from_cache(
            self._filter_supported_records(msg.questions))

        if len(questions_to_lookup) == 0 and len(answers_to_send) == 0:
            print("No supported question types to look up")
            return

        msg.str_repr()
        print(f'HAVE {len(questions_to_lookup)} questions to look up')

        if len(questions_to_lookup) == 0:
            print("Got answers from cache")
            self._respond_to_client(msg.header.id, client_addr, answers_to_send)
        else:
            self.cached_answers_by_query[(client_addr, msg.header.id)] = answers_to_send
            self._query_forwarder(msg.header.id, client_addr, questions_to_lookup)

    @staticmethod
    def _filter_supported_records(records):
        res = []
        for record in records:
            if record.type in types.values():
                res.append(record)
        return res

    def _get_answers_from_cache(self, questions):
        answers_to_send = []
        questions_to_lookup = []

        for question in questions:
            print(question.__dict__)
            cached_answers = self.cache.find_answers(question)
            if len(cached_answers) == 0:
                questions_to_lookup.append(question)
            answers_to_send += cached_answers

        return answers_to_send, questions_to_lookup

    def _query_forwarder(self, client_query_id, client_addr, questions_to_lookup):
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        client_socket.setblocking(False)
        self.forwarder_query_id += 1
        self.forwarder_query_id %= 1 << 16
        print(f'Query forwarder with ID = {self.forwarder_query_id}')

        query_to_forwarder = self.construct_query_from_questions(self.forwarder_query_id, questions_to_lookup)
        client_socket.sendto(query_to_forwarder.to_bytes(), self.FORWARDER_ADDR)
        self.selectors.register(
            client_socket, selectors.EVENT_READ,
            CallbackData(self._finish_query_to_forwarder,
                         client_socket, client_query_id, client_addr
                         )
        )

    def _finish_query_to_forwarder(self, client_socket, client_query_id, client_addr):
        print(f"Get response from {self.FORWARDER_ADDR}")
        byte_response, _ = client_socket.recvfrom(512)
        possible_parse, parsed_response = DnsMessage.try_parse(byte_response)
        self.selectors.unregister(client_socket)
        client_socket.close()

        if not possible_parse:
            print("Parsing error")
            return

        answers_from_cache = self.cached_answers_by_query[(client_addr, client_query_id)]
        del self.cached_answers_by_query[(client_addr, client_query_id)]
        answers_to_send = answers_from_cache + parsed_response.answers
        """print(f'Got {len(parsed_response.answers)} answers from forwarder')
        print(f'Got {len(parsed_response.authorities)} authorities from forwarder')
        print(f'Got {len(parsed_response.additions)} additions from forwarder')"""
        parsed_response.str_repr()


        records_to_cache = self._filter_supported_records(
            parsed_response.answers +
            parsed_response.authorities +
            parsed_response.additions)

        for record in records_to_cache:
            self.cache.add_answer(record)

        self._respond_to_client(client_query_id, client_addr, answers_to_send)

    def _respond_to_client(self, client_id, client_addr, answers):
        print(f"Answer to client id: {client_id}  ip: {client_addr[0]}  port: {client_addr[1]}")
        print()
        dns_response = self.construct_response_from_answers(client_id, answers)
        self.server_sock.sendto(dns_response.to_bytes(), client_addr)

    def stop(self):
        CacheManager().save_records(self.cache)
        super().stop()
