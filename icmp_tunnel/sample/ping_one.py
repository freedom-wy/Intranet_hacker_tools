# coding=utf-8
import socket
import struct


def calculate_checksum(icmp):
    if len(icmp) % 2:
        icmp += b'\00'

    checksum = 0
    for i in range(len(icmp) // 2):
        word, = struct.unpack('!H', icmp[2 * i:2 * i + 2])
        checksum += word

    while True:
        carry = checksum >> 16
        if carry:
            checksum = (checksum & 0xffff) + carry
        else:
            break

    checksum = ~checksum & 0xffff

    return struct.pack('!H', checksum)


def unpack_icmp_echo_reply(icmp):
    _type, code, _, ident, seq, = struct.unpack(
        '!BBHHH',
        icmp[:8]
    )
    if _type != 0:
        return
    if code != 0:
        return

    payload = icmp[8:]

    return ident, seq, payload


sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
payload = b"abcdefghijklmnopqrstuvwabcdefghi"
pseudo = struct.pack(
    '!BBHHH',
    8,
    0,
    0,
    1,
    1,
) + payload
checksum = calculate_checksum(pseudo)
print("pseudo前两位: {}, checksum的值为: {}, pseudo后面的值: {}".format(pseudo[:2], checksum, pseudo[4:]))
icmp = pseudo[:2] + checksum + pseudo[4:]
sock.sendto(icmp, 0, ('192.168.1.1', 0))

ip, (src_addr, _) = sock.recvfrom(1500)
print(ip[:2])

# unpack it
result = unpack_icmp_echo_reply(ip[20:])

# print info
_ident, seq, payload = result
print(_ident, seq, payload)
