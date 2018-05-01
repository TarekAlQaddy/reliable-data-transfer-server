import socket
import os
from enum import Enum
import random


class State(Enum):
    WAITING_0 = 0
    WAITING_1 = 1

saved_clients = {}
PACKET_SIZE = 30
HEADER_SIZE = 11
SERVER_PORT_NO = 12345
PLP = 0.2


def start(filename):
    main_socket = make_socket(SERVER_PORT_NO)
    start_listening(main_socket, PACKET_SIZE)


def make_socket(port_no):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('', port_no))
    return sock


def start_listening(main_socket, datagram_size):
    while True:
        data, address = main_socket.recvfrom(datagram_size)
        if data and address:
            main_socket.close()
            handle_received_packet(data, address)
        main_socket = make_socket(SERVER_PORT_NO)


def handle_received_packet(data, address):
    ip_address = address[0]
    port_no = address[1]
    print(address)
    if saved_clients.get(ip_address):
        print('process id: {}'.format(os.getpid()), data, address)
        current_state = saved_clients[ip_address]['state']
    else:
        saved_clients[ip_address] = {
            'state': State.WAITING_0
        }
        current_state = State.WAITING_0

    [headers, body] = data.decode().split('&$')
    [checksum, seq_no, is_final, is_ack] = [int(chars) for chars in headers.split('&')]

    if current_state == State(seq_no):
        ack_pkt = make_ack_packet(seq_no)
        sock = make_socket(SERVER_PORT_NO)
        sock.sendto(bytes(ack_pkt, 'UTF-8'), ('197.160.1.236', 12345))

        file = open('files/{}'.format(body), 'r')
        file_data = file.read()
        file_size = len(file_data)  # assuming ascii

        pointer = 0
        sending_seq_no = 0
        pkt_no = 1
        while pointer < file_size:
            pkt, pointer = make_pkt(file_data, file_size, sending_seq_no, pointer)

            if not lose_the_packet():
                sock.sendto(bytes(pkt, 'UTF-8'), ('197.160.1.236', 12345))
            acked = False
            while not acked:
                try:
                    sock.settimeout(4)
                    ack, addr = sock.recvfrom(PACKET_SIZE)
                    ack_data = ack.decode()
                    print('Pointer now {}'.format(pointer))
                    print('received ack {}'.format(ack_data))
                    if valid_ack(ack_data, sending_seq_no):
                        acked = True
                except socket.timeout:
                    print('Timeout, Resending packet #{}'.format(pkt_no))
                    sock.sendto(bytes(pkt, 'UTF-8'), ('197.160.1.236', 12345))

            sending_seq_no = 0 if sending_seq_no == 1 else 1
            pkt_no = pkt_no + 1
        print('File is successfully sent\n\n')
        # sock.close()


def valid_ack(ack_data, seq_no):
    ack_data_array = ack_data.split('&')
    print('checksumsss: {} {}'.format(calc_checksum(ack_data), ack_data_array[0]))
    return int(ack_data_array[1]) == seq_no and \
           int(ack_data_array[3]) == 1 and \
           int(calc_checksum(ack_data)) == int(ack_data_array[0])
    # return int(ack_data[1]) == seq_no and int(ack_data[3]) == 1


def make_ack_packet(seq_no):
    is_final = 0
    is_ack = 1
    checksum = calc_checksum('{}&{}&{}&{}&$'.format(255, seq_no, is_final, is_ack))
    print('ack checksum {}'.format(checksum))
    headers = '{}&{}&{}&{}&$'.format(checksum, seq_no, is_final, is_ack)
    return headers


def make_pkt(data, size, seq_no, pointer):
    is_final = 0
    if size - pointer > PACKET_SIZE - HEADER_SIZE:
        body = data[pointer: pointer + PACKET_SIZE - HEADER_SIZE]
    else:
        is_final = 1
        body = data[pointer: len(data)]

    headers_for_checksum = '{}&{}&{}&{}&$'.format(255, seq_no, is_final, 0)
    checksum = calc_checksum(headers_for_checksum + body)
    headers = '{}&{}&{}&{}&$'.format(checksum, seq_no, is_final, 0)
    pkt = headers + body

    pointer = pointer + len(body)
    print('Headers: {}'.format(headers.split('&')))
    print('Body: {}'.format(body))

    return pkt, pointer


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
