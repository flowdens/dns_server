import struct
from dns.ResourceRecord import Question, ResourceRecord
from dns.general_func import unpack_16b


class Header:
    def __init__(self):
        self.id = 0  # 16b
        self.type = 0  # 1b 0=Query,1=Response
        self.op_code = 0  # 4b 0=Query, 1=InversedQuery, 2=Status(запрос статуса сервера)
        self.is_auth = 0  # 1b
        self.is_truncated = 0  # 1b
        self.rec_desired = 0  # 1b
        self.rec_available = 0  # 1b
        self.z = 0  # 3b
        self.response_code = 0  # 4b 0=NoError, 1=FormatError, 2=ServerFailure,

        self.qdcount = 0    # 16b
        self.ancount = 0    # 16b
        self.nscount = 0    # 16b
        self.arcount = 0    # 16b

    def _flags_to_bytes(self):
        flags = self.type << 15
        flags |= self.op_code << 11
        flags |= self.is_auth << 10
        flags |= self.is_truncated << 9
        flags |= self.rec_desired << 8
        flags |= self.rec_available << 7
        flags |= self.response_code
        return flags

    def _parse_flags(self, bts):
            self.type = (bts >> 15) & 0b1
            self.op_code = (bts >> 11) & 0b1111
            self.is_auth = (bts >> 10) & 0b1
            self.is_truncated = (bts >> 9) & 0b1
            self.rec_desired = (bts >> 8) & 0b1
            self.rec_available = (bts >> 7) & 0b1
            self.response_code = bts & 0b1111

    def to_bytes(self):
        flags = self._flags_to_bytes()
        return struct.pack('!HHHHHH', self.id, flags, self.qdcount, self.ancount, self.nscount, self.arcount)

    def parse(self, bts):
        self.id = unpack_16b(bts[:2])
        self._parse_flags(unpack_16b(bts[2:4]))
        self.qdcount = unpack_16b(bts[4:6])
        self.ancount = unpack_16b(bts[6:8])
        self.nscount = unpack_16b(bts[8:10])
        self.arcount = unpack_16b(bts[10:12])


class DnsMessage:
    def __init__(self):
        self.header = Header()
        self.questions = []
        self.answers = []
        self.authorities = []
        self.additions = []

    @staticmethod
    def try_parse(bts):
        try:
            msg = DnsMessage.parse(bts)
            return True, msg
        except Exception:
            return False, None

    @staticmethod
    def parse(bts):
        msg = DnsMessage()
        msg.header.parse(bts)
        offset, msg.questions = Question.decode_questions(bts, 12, msg.qdcount)
        offset, msg.answers = ResourceRecord.decode_answers(bts, offset, msg.ancount)
        offset, msg.authorities = ResourceRecord.decode_answers(bts, offset, msg.nscount)
        offset, msg.additions = ResourceRecord.decode_answers(bts, offset, msg.arcount)
        return msg

    def to_bytes(self):
        b_header = self.header.to_bytes()
        b_questions = self.rr_to_bytes(self.questions)
        b_answers = self.rr_to_bytes(self.answers)
        b_authorities = self.rr_to_bytes(self.authorities)
        b_additions = self.rr_to_bytes(self.additions)
        return b_header + b_questions + b_answers + b_authorities + b_additions

    @staticmethod
    def rr_to_bytes(records):
        return b''.join([record.to_bytes() for record in records])


