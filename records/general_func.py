import struct


def encode_name(name):
    encoded_name = bytearray()
    labels = name.split('.')
    for label in labels:
        encoded_name.append(len(label))
        encoded_name += bytearray(label.encode('ascii'))
    return bytes(encoded_name)


def decode_name(bts, offset):
    labels = []
    pointer_mask = 0b11 << 6

    while bts[offset] != 0:
        label = bytearray()
        length = int(bts[offset])
        if length & pointer_mask != 0:
            reduce_mask = (1 << 16) - (0b11 << 14) - 1
            pointer = unpack_16b(bts[offset:offset + 2]) & reduce_mask
            prefix = '' if len(labels) == 0 else '.'.join(labels) + '.'
            return offset + 2, prefix + decode_name(bts, pointer)[1]

        for i in range(1, length + 1):
            label.append(bts[offset + i])
        offset += length + 1
        labels.append(label.decode('ascii'))
    labels.append('')
    return offset + 1, '.'.join(labels)


def unpack_16b(bts):
    # H - 16b
    return struct.unpack('!H', bts)[0]
