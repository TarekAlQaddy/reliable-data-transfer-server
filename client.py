import socket

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

data = bytes('2\r5\r0\r0\r1\r0\r\nx.txt', 'UTF-8')

sock.bind(('192.168.1.6', 12345))
sock.sendto(data, ('197.165.182.242', 12345))


while True:
    data, addr = sock.recvfrom(1024)
    print(data, addr)
