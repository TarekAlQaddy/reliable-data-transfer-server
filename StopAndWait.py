import socket
import os
from enum import Enum
import random


class State(Enum):
    WAITING_0 = 0
    WAITING_1 = 1

saved_clients = {}
PACKET_SIZE = 30
HEADER_SIZE = 13
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
        if int(data.decode().split('\r')[5]):
            print('received ACK')
        if data and address:
            main_socket.close()
            handle_received_packet(data, address)
            # t = threading.Thread(target=handle_received_packet, args=(data, address))
            # t.start()
            # pid = os.fork()
            # if pid == 0:
            #     handle_received_packet(data, address)
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

    [headers, body] = data.decode().split('\r\n')
    [checksum, length, seq_no, pkt_no, is_final, is_ack] = [int(chars) for chars in headers.split('\r')]

    if current_state == State(seq_no):
        ack_pkt = make_ack_packet(seq_no)
        sock = make_socket(SERVER_PORT_NO)
        sock.sendto(bytes(ack_pkt, 'UTF-8'), (ip_address, port_no))

        file = open('files/{}'.format(body), 'r')
        file_data = file.read()

        file_size = len(file_data)  # assuming ascii

        pointer = 0
        sending_seq_no = 0
        pkt_no = 1
        while pointer < file_size:
            pkt, pointer = make_pkt(file_data, file_size, sending_seq_no, pointer, pkt_no)
            # print('Sending {}'.format(bytes(pkt)))
            # print(ip_address)
            # print(port_no)
            if not lose_the_packet():
                sock.sendto(bytes(pkt, 'UTF-8'), (ip_address, port_no))
            acked = False
            while not acked:
                try:
                    sock.settimeout(4)
                    ack, addr = sock.recvfrom(PACKET_SIZE)
                    ack_data = ack.decode().split('\r')
                    print('Pointer now {}'.format(pointer))
                    print('received ack {}'.format(ack_data))
                    if valid_ack(ack_data, sending_seq_no):
                        acked = True
                except socket.timeout:
                    print('Timeout, Resending packet #{}'.format(pkt_no))
                    sock.sendto(bytes(pkt, 'UTF-8'), (ip_address, port_no))

            sending_seq_no = 0 if sending_seq_no == 1 else 1
            pkt_no = pkt_no + 1
        print('File is successfully sent\n\n')
        sock.close()


def valid_ack(ack_data, seq_no):
    # TODO int(ack_data[2]) == seq_no and int(ack_data[5]) == 1 and calc_checksum(ack_data) == ack_data[0]
    return int(ack_data[2]) == seq_no and int(ack_data[5]) == 1


def make_ack_packet(seq_no):
    checksum = 1
    pkt_no = is_final = length = 0
    is_ack = 1
    headers = '{}\r{}\r{}\r{}\r{}\r{}\r\n'.format(checksum, length, seq_no, pkt_no, is_final, is_ack)
    return headers


def make_pkt(data, size, seq_no, pointer, pkt_no):

    checksum = 255
    headers_without_length = '{}\r{}\r{}\r{}\r{}\r\n'.format(checksum, seq_no, pkt_no, 0, 0)
    headers_size = len(headers_without_length)
    headers_size += len(str(headers_size))
    is_final = 0
    if size - pointer > PACKET_SIZE - headers_size:
        body = data[pointer: pointer + PACKET_SIZE - headers_size]
    else:
        is_final = 1
        body = data[pointer: len(data)]

    pkt_size = len(body) + headers_size
    headers_for_checksum = '{}\r{}\r{}\r{}\r{}\r{}\r\n'.format(255, pkt_size, seq_no, pkt_no, is_final, 0)
    checksum = calc_checksum(headers_for_checksum + body)
    headers = '{}\r{}\r{}\r{}\r{}\r{}\r\n'.format(checksum, pkt_size, seq_no, pkt_no, is_final, 0)
    pkt = headers + body

    pointer = pointer + len(body)
    print('Headers: {}'.format(headers.split('\r')))
    print('Body: {}'.format(body))

    return pkt, pointer


def calc_checksum(data):
    data = data[3:]
    all_sum = sum(bytearray(data, 'UTF-8'))
    cutted_sum = all_sum & 0x000000FF
    remaining = all_sum >> 8
    while remaining != 0:
        cutted_sum += (remaining & 0x000000FF)
        while (cutted_sum & 0x0000FF00) != 0:
            cutted_sum = (cutted_sum + ((cutted_sum & 0x0000FF00) >> 8))
        remaining = remaining >> 8

    print('cutted sum: {}'.format(cutted_sum))
    return cutted_sum ^ 0xFF


def lose_the_packet():
    return random.random() < PLP

start('ss')
