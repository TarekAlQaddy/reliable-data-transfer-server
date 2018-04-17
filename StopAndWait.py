import socket
import os
from enum import Enum
import binascii


class State(Enum):
    WAITING_0 = 0
    WAITING_1 = 1

saved_clients = {}
PACKET_SIZE = 30
HEADER_SIZE = 13


def start(filename):
    port = 12345
    main_socket = make_socket(port)
    start_listening(main_socket, PACKET_SIZE)


def make_socket(port_no):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('', port_no))
    return sock


def start_listening(main_socket, datagram_size):
    while True:
        data, address = main_socket.recvfrom(datagram_size)
        if data and address:
            pid = os.fork()
            if pid == 0:
                handle_received_packet(data, address)


def handle_received_packet(data, address):
    ip_address = address[0]
    port_no = address[1]
    if saved_clients.get(ip_address):
        print('process id: {}'.format(os.getpid()), data, address)
        current_state = saved_clients[ip_address]['state']
    else:
        saved_clients[ip_address] = {
            'state': State.WAITING_0
        }
        current_state = State.WAITING_0

    [headers, body] = data.decode().split('\r\n')
    [checksum, length, seq_no, pkt_no, no_of_pkts, is_ack] = [int(chars) for chars in headers.split('\r')]

    if current_state == State(seq_no):
        ack_pkt = make_ack_packet(seq_no)
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.sendto(bytes(ack_pkt, 'UTF-8'), (ip_address, port_no))

        file = open('files/{}'.format(body), 'r')
        file_data = file.read()

        file_size = len(file_data)  # assuming ascii

        pointer = 0
        sending_seq_no = 0
        pkt_no = 0
        while pointer < file_size:
            pkt, pointer = make_pkt(file_data, file_size, sending_seq_no, pointer, pkt_no, (file_size // PACKET_SIZE) + 1)
            pkt_no = pkt_no + 1
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.sendto(bytes(pkt, 'UTF-8'), (ip_address, port_no))

            # TODO: set timeout for ack and resend
            print('entered', pointer)
            sending_seq_no = 0 if sending_seq_no == 1 else 1


def make_ack_packet(seq_no):
    checksum = 0x15
    length = HEADER_SIZE
    pkt_no = no_of_pkts = 0
    is_ack = 1
    headers = '{}\r{}\r{}\r{}\r{}\r{}\r\n'.format(checksum, length, seq_no, pkt_no, no_of_pkts, is_ack)
    return headers


def make_pkt(data, size, seq_no, pointer, pkt_no, no_of_packets):
    if size - pointer > PACKET_SIZE - HEADER_SIZE:
        body = data[pointer: pointer + PACKET_SIZE - HEADER_SIZE]
    else:
        body = data[pointer: len(data)]
    checksum = 0x12
    print(len(body))
    pkt_size = len(body) + HEADER_SIZE
    headers = '{}\r{}\r{}\r{}\r{}\r{}\r\n'.format(checksum, pkt_size, seq_no, pkt_no, no_of_packets, 0)

    pkt = headers + body

    pointer = pointer + len(body)
    print(pointer)

    return pkt, pointer



start('gg')
