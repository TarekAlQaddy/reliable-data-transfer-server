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


def encrypt(message, key):
    # convert to uppercase.
    # strip out non-alpha characters.
    message = filter(str.isalpha, message.upper())

    # single letter encrpytion.
    def enc(c, k): return chr(((ord(k) + ord(c) - 2 * ord('A')) % 26) + ord('A'))

    return "".join(starmap(enc, zip(message, cycle(key))))


def print_progress_bar(iteration, total, prefix='', suffix='', decimals=1, length=100, fill='█'):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
    """
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filled_length = int(length * iteration // total)
    bar = fill * filled_length + '-' * (length - filled_length)
    print('\r%s |%s| %s%% %s' % (prefix, bar, percent, suffix), end='\r')
    # Print New Line on Complete
    if iteration == total:
        print()
