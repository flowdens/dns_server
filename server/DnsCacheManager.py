from dns.DnsMesssage import DnsMessage


class CacheManager:
    def handle_packet(self, bts):
        possible_parse, msg = DnsMessage.try_parse(bts)

        if not possible_parse:
            print("Parsing error")
            return

        try:
            self.handle_query_message(msg)
        except Exception:
            self.construct_failure_msg(msg)

        return msg

    def handle_query_message(self, msg):
        pass

    @staticmethod
    def construct_failure_msg(response):
        response.header.type = 1
        response.header.response_code = 2

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
    def construct_response_from_answers(response_id, answers):
        response = DnsMessage()
        response.header.id = response_id
        response.header.type = 1
        response.header.ancount = len(answers)
        response.answers = answers
        return response