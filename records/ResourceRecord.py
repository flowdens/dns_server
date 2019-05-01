import struct
from dns.config import types
from dns.general_func import encode_name, decode_name, unpack_16b


class Question:
    def __init__(self, name, tp, cl):
        self.name = name
        self.type = tp
        self.class_ = cl

    def to_bytes(self):
        return encode_name(self.name) + struct.pack('!HH', self.type, self.class_)

    @staticmethod
    def decode_questions(bts, offset, qdcount):
        questions = []
        for i in range(qdcount):
            offset, name = decode_name(bts, offset)
            tp = unpack_16b(bts[offset:offset + 2])
            cl = unpack_16b(bts[offset + 2:offset + 4])
            offset += 4
            questions.append(Question(name, tp, cl))

        return offset, questions


class ResourceRecord:
    def __init__(self, name=None, tp=0, cl=0, ttl=0, data=None):
        self.name = name
        self.type = tp
        self.class_ = cl
        self.ttl = ttl
        self.data = data

    @staticmethod
    def decode_answers(bts, offset, count):
        answers = []
        for i in range(count):
            offset, answer = ResourceRecord._decode_answer(bts, offset)
            answers.append(answer)
        return offset, answers

    @staticmethod
    def _decode_answer(bts, offset):
        # I = 32b
        offset, name = decode_name(bts, offset)
        tp = unpack_16b(bts[offset:offset + 2])
        cl = unpack_16b(bts[offset + 2:offset + 4])
        ttl = struct.unpack('!I', bts[offset + 4:offset + 8])[0]
        rdlen = unpack_16b(bts[offset + 8:offset + 10])

        offset += 10

        if tp == types['A']:
            data = ResourceRecord._decode_a_data(bts, offset)
        elif tp == types['NS']:
            data = ResourceRecord._decode_ns_data(bts, offset)
        else:
            data = bts[offset:offset + rdlen]

        offset += rdlen
        return offset, ResourceRecord(name, tp, cl, ttl, data)

    @staticmethod
    def _decode_a_data(bts, offset):
        # B = 8b
        data = bts[offset:offset + 4]
        ip_parts = struct.unpack('!BBBB', data)
        return '.'.join(map(str, ip_parts))

    @staticmethod
    def _decode_ns_data(bts, offset):
        return decode_name(bts, offset)[1]

    def to_bytes(self):
        # H = 16b, I = 32b
        prefix = encode_name(self.name) + \
                 struct.pack('!HHI', self.type, self.class_, self.ttl)

        if self.type == types['A']:
            encoded_data = ResourceRecord._encode_a_data(self.data)
        elif self.type == types['NS']:
            encoded_data = ResourceRecord._encode_ns_data(self.data)

        r_data_len = len(encoded_data)
        return prefix + struct.pack('!H', r_data_len) + encoded_data

    @staticmethod
    def _encode_a_data(ip):
        ip_bytes = [struct.pack('!B', int(ip_part)) for ip_part in ip.split('.')]
        return b''.join(ip_bytes)

    @staticmethod
    def _encode_ns_data(domain_name):
        return encode_name(domain_name)
