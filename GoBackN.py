import socket
import math
import time
import threading
from Helpers import PacketState, calc_checksum, lose_the_packet, make_ack_packet


PACKET_SIZE = 200
HEADER_SIZE = 12
SERVER_PORT_NO = None
PLP = None
WINDOW_SIZE = None
MAX_SEQ_NO = None

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
    global SERVER_PORT_NO, WINDOW_SIZE, MAX_SEQ_NO, PLP
    file = open(filename, 'r')
    configs = file.read()
    configs = configs.split('\n')
    SERVER_PORT_NO = int(configs[0].split(':')[1].strip())
    WINDOW_SIZE = int(configs[1].split(':')[1].strip())
    MAX_SEQ_NO = WINDOW_SIZE
    PLP = float(configs[2].split(':')[1].strip())
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
    time.sleep(0.1)
    print('Base {}'.format(state['base']))
    print('timout {}'.format(pkt_index))
    main_lock.acquire()
    if int(state['base']) == int(pkt_index) and state['packets'][pkt_index] != 2:  # still didn't acknowledge, Resend
        print('{} Same as base'.format(state['base']))
        for i in range(state['base'], state['base'] + WINDOW_SIZE):
            if not lose_the_packet(PLP):
                thread = threading.Thread(target=send_packet, args=(sock, state['packets'][i], i, address))
                thread.start()
                threads.append(thread)
    # print('{} status'.format(state['packets'][pkt_index].status))

    main_lock.release()
    return


def handle_received_packet(sock, packet, address):
    received_seq_no = packet.decode().split('&')[1]
    print('Handling seq no {}'.format(received_seq_no))
    main_lock.acquire()
    if int(state['packets'][state['base']].seq_no) == int(received_seq_no):
        print('FOUND {}'.format(received_seq_no))
        state['packets'][state['base']].status = 2
        state['acks_count'] += 1
        state['base'] += 1
    print('Base now: {}'.format(state['base']))
    main_lock.release()
    main_lock.acquire()
    base = state['base']
    last_index = base + WINDOW_SIZE - 1
    if state['packets'][last_index].status == 0:
        main_lock.release()
        thread = threading.Thread(target=send_packet, args=(sock, state['packets'][last_index], last_index, address))
        thread.start()
        threads.append(thread)
    else:
        main_lock.release()
    print('\nAcks count: {}\n'.format(state['acks_count']))
    main_lock.acquire()
    if state['acks_count'] == len(state['packets']) - 1:
        print('File Successfully Sent.')
    main_lock.release()
    return


def valid_ack(packet):
    # print('CHECKSUM: {}'.format(packet))
    return calc_checksum(packet.decode()) == packet.decode().split('&')[0]


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
