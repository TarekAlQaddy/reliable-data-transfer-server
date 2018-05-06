import socket
import os
from enum import Enum
from Helpers import calc_checksum, make_ack_packet, lose_the_packet, encrypt, print_progress_bar


class State(Enum):
    WAITING_0 = 0
    WAITING_1 = 1

saved_clients = {}
PACKET_SIZE = 200
HEADER_SIZE = 12
SERVER_PORT_NO = None
PLP = None


def start(filename):
    global SERVER_PORT_NO, PLP
    file = open(filename, 'r')
    configs = file.read()
    configs = configs.split('\n')
    SERVER_PORT_NO = int(configs[0].split(':')[1].strip())
    PLP = float(configs[2].split(':')[1].strip())
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
        sock.sendto(bytes(ack_pkt, 'UTF-8'), address)

        file = open('files/{}'.format(body), 'r')
        file_data = file.read()
        file_size = len(file_data)  # assuming ascii

        pointer = 0
        sending_seq_no = 0
        pkt_no = 1
        while pointer < file_size:
            pkt, pointer = make_pkt(file_data, file_size, sending_seq_no, pointer)

            if not lose_the_packet(PLP):
                sock.sendto(bytes(pkt, 'UTF-8'), address)
            acked = False
            while not acked:
                try:
                    sock.settimeout(0.1)
                    ack, addr = sock.recvfrom(PACKET_SIZE)
                    ack_data = ack.decode()
                    print('Sending Packet #{}'.format(pkt_no))
                    if valid_ack(ack_data, sending_seq_no):
                        print_progress_bar(pointer, file_size)
                        acked = True
                except socket.timeout:
                    print('Timeout, Resending packet #{}'.format(pkt_no))
                    sock.sendto(bytes(pkt, 'UTF-8'), address)

            sending_seq_no = 0 if sending_seq_no == 1 else 1
            pkt_no = pkt_no + 1
        print('File is successfully sent\n\n')


def valid_ack(ack_data, seq_no):
    ack_data_array = ack_data.split('&')
    return int(ack_data_array[1]) == int(seq_no) and \
           int(ack_data_array[3]) == 1 and \
           int(calc_checksum(ack_data)) == int(ack_data_array[0])


def make_pkt(data, size, seq_no, pointer):
    is_final = 0
    if size - pointer > PACKET_SIZE - HEADER_SIZE:
        body = data[pointer: pointer + PACKET_SIZE - HEADER_SIZE]
    else:
        is_final = 1
        body = data[pointer: len(data)]

    headers_for_checksum = '{}&{}&{}&{}&$'.format(255, str(seq_no).zfill(2), is_final, 0)
    checksum = calc_checksum(headers_for_checksum + body)
    headers = '{}&{}&{}&{}&$'.format(checksum, str(seq_no).zfill(2), is_final, 0)

    pkt = headers + body

    pointer = pointer + len(body)
    return pkt, pointer
