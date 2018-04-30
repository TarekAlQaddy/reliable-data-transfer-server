import socket

ip = ""
port = 40000

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

sock.bind((ip, port))
# sock.listen(5)
# while True:
#     data, address = sock.recvfrom(1024)
#     print(data, address)
sock.sendto(bytes('2\r5\r0\r0\r1\r0\r\na.txt', 'UTF-8'), ('localhost', 12345))
while True:
    data, addr = sock.recvfrom(30)
    sock.sendto(bytes('2\r5\r{}\r0\r1\r1\r\n'.format(data.decode().split('\r')[2]), 'UTF-8'), ('localhost', 12345))
    print(data, addr)

# sock.bind(('', port))

# while True:
#     data, addr = sock.recvfrom(30)
#     sock.sendto(bytes('2\r5\r0\r0\r1\r1\r\n', 'UTF-8'), ('localhost', 12345))
#     print(data, addr)
#
#     data, addr = sock.recvfrom(30)
#     sock.sendto(bytes('2\r5\r1\r0\r1\r1\r\n', 'UTF-8'), ('localhost', 12345))
#     print(data, addr)

# sock.sendto(bytes('2\r5\r0\r0\r1\r1\r\n', 'UTF-8'), ('localhost', 12345))
# sock.sendto(bytes('two', 'UTF-8'), ('localhost', 12345))
# sock.sendto(bytes('three', 'UTF-8'), ('localhost', 12345))
