import socket
import random
import math
import time
import threading


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


saved_clients = {}
PACKET_SIZE = 50
HEADER_SIZE = 12
SERVER_PORT_NO = 12345
PLP = 0.2
WINDOW_SIZE = 3
MAX_SEQ_NO = 9

main_lock = threading.Lock()
threads = []

state = {
    'base': 0,
    'packets': [],
    'acks_count': 0
}

# States:
# 0: not sent
# 1: sent
# 2: acked


def start(filename):
    main_socket = make_socket(SERVER_PORT_NO)
    start_listening(main_socket, PACKET_SIZE)


def make_socket(port_no):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('', port_no))
    return sock


def start_listening(main_socket, datagram_size):
    file_data, address = main_socket.recvfrom(datagram_size)

    ack_pkt = make_ack_packet(0)
    main_socket.sendto(bytes(ack_pkt, 'UTF-8'), address)

    file = open('files/{}'.format(file_data.decode().split('&$')[1]))
    file_data = file.read()
    no_of_pkts = int(math.ceil(len(file_data) / (PACKET_SIZE - HEADER_SIZE)))

    seq_no = 0
    step_size = PACKET_SIZE - HEADER_SIZE
    for i in range(no_of_pkts):
        if no_of_pkts - 1 == i:
            current_data = file_data[i*step_size:len(file_data)]
            is_final = 1
        else:
            current_data = file_data[i*step_size:i*step_size+step_size]
            is_final = 0
        pkt = PacketState(seq_no, 0, is_final, current_data)
        state['packets'].append(pkt)
        seq_no = (seq_no + 1) % MAX_SEQ_NO

    for i in range(WINDOW_SIZE):
        thread = threading.Thread(target=send_packet, args=(main_socket, state['packets'][i], i, address))
        thread.start()
        threads.append(thread)

    print('Sent first window size')

    while True:
        rPkt, rAddress = main_socket.recvfrom(PACKET_SIZE)
        print('Received ack {}'.format(rPkt.decode()))
        thread = threading.Thread(target=handle_received_packet, args=(main_socket, rPkt, rAddress))
        thread.start()
        threads.append(thread)
        check_if_thread_finished()


def send_packet(sock, pkt, pkt_index, address):
    print('Sending seq no {}'.format(pkt.seq_no))
    main_lock.acquire()
    if state['packets'][pkt_index].status != 2:
        sock.sendto(bytes(pkt.packet, 'UTF-8'), address)
    else:
        main_lock.release()
        return
    pkt.status = 1
    main_lock.release()
    time.sleep(2)
    main_lock.acquire()
    acked = True
    if int(state['packets'][pkt_index].status) != 2:  # still didn't acknowledge, Resend
        acked = False
        main_lock.release()
        thread = threading.Thread(target=send_packet, args=(sock, pkt, pkt_index, address))
        thread.start()
        threads.append(thread)
        # send_packet(sock, pkt, pkt_index, address)
    if acked:
        main_lock.release()
    return


def handle_received_packet(sock, packet, address):
    received_seq_no = packet.decode().split('&')[1]
    print('Handling seq no {}'.format(received_seq_no))

    base_index = state['base']
    max_index = state['base'] + WINDOW_SIZE
    main_lock.acquire()
    for i in range(base_index, max_index):
        if int(state['packets'][i].seq_no) == int(received_seq_no) and \
                        int(state['packets'][i].status) != 2 and valid_ack(packet):
            print('Found index#{}'.format(i))
            state['packets'][i].status = 2
            state['acks_count'] += 1
            break
    main_lock.release()
    print('\nAcks count: {}\n'.format(state['acks_count']))
    main_lock.acquire()
    if state['acks_count'] == len(state['packets']) - 1:
        print('File Successfully Sent.')
    main_lock.release()
    check_if_advancing_needed(sock, address)


def valid_ack(packet):
    # print('CHECKSUM: {}'.format(packet))
    return calc_checksum(packet.decode()) == packet.decode().split('&')[0]


def check_if_advancing_needed(sock, address):
    main_lock.acquire()
    print('Entered advancing')
    print('base Now: {}'.format(state['base']))
    count = 0
    while state['packets'][state['base']].status == 2 and count < WINDOW_SIZE \
            and state['base'] + WINDOW_SIZE < len(state['packets']):
        print('Advancing found')
        count += 1
        state['base'] += 1
    main_lock.release()
    start = state['base']
    end = state['base'] + WINDOW_SIZE
    for i in range(start, end):
        # print(state['packets'][i].status)
        main_lock.acquire()
        if state['packets'][i].status == 0:
            main_lock.release()
            print('New packets being sent {}'.format(i))
            thread = threading.Thread(target=send_packet, args=(sock, state['packets'][i], i, address))
            thread.start()
            threads.append(thread)
        else:
            main_lock.release()


def check_if_thread_finished():
    print('Threads Count: {}'.format(len(threads)))
    print('Inactive Count: {}'.format(threading.active_count()))
    inactive = []
    for th in threads:
        if not th.is_alive():
            inactive.append(th)
            threads.remove(th)

    for i in inactive:
        i.join()

    print('Threads Count: {}'.format(len(threads)))
    print('Inactive Count: {}'.format(threading.active_count()))
    # for th in inactive:
    #     th.join()


def make_ack_packet(seq_no):
    is_final = 0
    is_ack = 1
    checksum = calc_checksum('{}&{}&{}&{}&$'.format(255, seq_no, is_final, is_ack))
    print('ack checksum {}'.format(checksum))
    headers = '{}&{}&{}&{}&$'.format(checksum, str(seq_no).zfill(2), is_final, is_ack)
    return headers


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


def lose_the_packet():
    return False
    # TODO: return random.random() < PLP


start('ss')
