import datetime
from datetime import date
import functools
import json
from threading import Lock
from records.ResourceRecord import ResourceRecord


def synchronized(lock=None):
    def decorator(wrapped):
        @functools.wraps(wrapped)
        def wrapper(*args, **kwargs):
            with lock:
                return wrapped(*args, **kwargs)
        return wrapper
    return decorator


class CacheItem:
    def __init__(self, data, ttl, cached_at=None):
        self.data = data
        self.ttl = ttl

        if cached_at is not None:
            self.cached_at = cached_at
        else:
            self.cached_at = datetime.datetime.now()


class Cache:
    def __init__(self):
        self.buffer = dict()
        self.cache_lock = Lock()
        self.add_answer = synchronized(self.cache_lock)(self.add_answer)
        self.find_answers = synchronized(self.cache_lock)(self.find_answers)

    def add_answer(self, record, cached_at=None):
        key = (record.name, record.type, record.class_)
        if key not in self.buffer.keys():
            self.buffer[key] = []
        self.buffer[key].append(CacheItem(record.data, record.ttl, cached_at))

    def find_answers(self, question):
        key = (question.name, question.type, question.class_)
        if key in self.buffer.keys():
            records = self.buffer[key]
            alive_records = self._get_alive_records(records)
            result = [ResourceRecord(*(key + (record.ttl, record.data))) for record in alive_records]

            self.buffer[key] = alive_records
            return result
        return []

    @staticmethod
    def _get_alive_records(records):
        alive_records = []
        for record in records:
            expires_at = record.cached_at + datetime.timedelta(seconds=record.ttl)
            if datetime.datetime.now() < expires_at:
                alive_records.append(record)
        return alive_records


class CacheManager:
    FIELDS = ['name', 'type', 'class_', 'ttl', 'data', 'cached_at', "__RR__"]
    file = "cache.json"

    def save_records(self, cache):
        with open(self.file, "w") as write_file:
            for key, values in cache.buffer.items():
                for val in values:
                    json.dump(
                        dict(zip(self.FIELDS, [key[0], key[1], key[2], val.ttl, val.data, val.cached_at.strftime('%Y-%m-%d %H:%M:%S.%f'), True])),
                        write_file)
                    write_file.write('\n')

    def decode_rr(self, dct):
        if "__RR__" in dct:
            print("decode")
            cached_at = datetime.datetime.strptime(dct['cached_at'], '%Y-%m-%d %H:%M:%S.%f')
            print(dct["name"], dct["type"], dct["class_"], dct["ttl"], dct["data"], cached_at)
            print()

            return ResourceRecord(
                dct["name"], dct["type"],
                dct["class_"], dct["ttl"], dct["data"]
            ), cached_at
        return dct

    def load_records(self):
        cache = Cache()
        with open(self.file, "r") as read_file:
            for line in read_file.readlines():
                item = json.loads(line, object_hook=self.decode_rr)
                if item == {}:
                    continue
                cache.add_answer(item[0], item[1])
        return cache

    """"@staticmethod
    def load_cache_from(file_name):
        cache = Cache()

        with open(file_name, 'r', encoding='utf-8') as csv_cache:
            reader = DictReader(csv_cache, CsvCacheManager.FIELDS)
            next(reader)
            for row in reader:
                cached_at = datetime.datetime.strptime(row['cached_at'], '%Y-%m-%d %H:%M:%S.%f')
                cache.add_answer(
                    ResourceRecord(row['name'], int(row['tp']), int(row['cl']),
                        int(row['ttl']), row['data']), cached_at)
        return cache

    @staticmethod
    def save_cache_to(cache, file_name):
        with open(file_name, 'w', encoding='utf-8') as csv_cache:
            with cache.cache_lock:
                writer = DictWriter(csv_cache, CsvCacheManager.FIELDS)
                writer.writeheader()

                for name, tp, cl in cache.cache.keys():
                    for item in cache.cache[(name, tp, cl)]:
                        writer.writerow(
                            {
                                'name': name, 'tp': tp, 'cl': cl,
                                **item.__dict__
                            }) """
