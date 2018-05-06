import random
from itertools import starmap, cycle


class PacketState:
    def __init__(self, seq_no, status, is_final, data):
        self.seq_no = seq_no
        self.status = status
        self.data = data
        self.packet = PacketState.make_pkt(data, seq_no, is_final)

    @staticmethod
    def make_pkt(data, seq_no, is_final):
        checksum_headers = '{}&{}&{}&{}&$'.format(255, str(seq_no).zfill(2), is_final, 0)
        checksum = calc_checksum(checksum_headers + data)
        headers = '{}&{}&{}&{}&$'.format(checksum, str(seq_no).zfill(2), is_final, 0)
        return headers + data


def calc_checksum(data):
    data = data[3:]
    all_sum = 0
    for s in data:
        all_sum += ord(s)
    cutted_sum = all_sum & 0x000000FF
    remaining = all_sum >> 8
    while remaining != 0:
        cutted_sum += (remaining & 0x000000FF)
        while (cutted_sum & 0x0000FF00) != 0:
            next_byte = (cutted_sum & 0x0000FF00) >> 8
            cutted_sum &= 0x000000FF
            cutted_sum += next_byte
        remaining = remaining >> 8
    cutted_sum = cutted_sum ^ 0xFF
    cutted_sum = str(cutted_sum).zfill(3)
    return cutted_sum


# def make_ack_packet(seq_no):
#     is_final = 0
#     is_ack = 1
#     checksum = calc_checksum('{}&{}&{}&{}&$'.format(255, seq_no, is_final, is_ack))
#     print('ack checksum {}'.format(checksum))
#     headers = '{}&{}&{}&{}&$'.format(checksum, seq_no, is_final, is_ack)
#     return headers

def make_ack_packet(seq_no):
    is_final = 0
    is_ack = 1
    checksum = calc_checksum('{}&{}&{}&{}&$'.format(255, seq_no, is_final, is_ack))
    print('ack checksum {}'.format(checksum))
    headers = '{}&{}&{}&{}&$'.format(checksum, str(seq_no).zfill(2), is_final, is_ack)
    return headers


def lose_the_packet(PLP):
    # return False
    return random.random() < PLP


def corrupt_pkt(pkt):
    headers = pkt[0:12]
    data = pkt[12:]
    for i in range(12, len(pkt)):
        if random.random() > 0.5:
            data[i] &= 0x01010101

    return headers + data


def encrypt(message, key):
    # convert to uppercase.
    # strip out non-alpha characters.
    message = filter(str.isalpha, message.upper())

    # single letter encrpytion.
    def enc(c, k): return chr(((ord(k) + ord(c) - 2 * ord('A')) % 26) + ord('A'))

    return "".join(starmap(enc, zip(message, cycle(key))))
