# coding=utf-8
import md5
import sys
import time
import Queue
import random
import select
import socket
import struct
import threading
from handle_log import logger

gSOCKETID = []
gCLIENTOBJ = []
ICMPSOCK = None

VER = '\x01\x01'
HANDSHAKE = 'HELLO'


class IcmpSocket:
    def __init__(self, MODE):
        self.ICMP_ECHO_REQUEST = 0x08
        self.ICMP_ECHO_REPLY = 0x00
        if MODE == 0:
            self.ICMP_SEND = self.ICMP_ECHO_REPLY
            self.ICMP_RECV = self.ICMP_ECHO_REQUEST
            self.ICMP_CODE = 0x00
        else:
            self.ICMP_RECV = self.ICMP_ECHO_REPLY
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
            # 为什么要加28
            packet, addr = self.sock.recvfrom(buffsize + 28)
            # 跳过IP头部的20字节，找到ICMP头部8个字节，type1,code1,checksum2,id2,seq2
            icmpHeader = packet[20:28]
            # 解包
            type, code, checksum, packetID, sequence = struct.unpack(
                "bbHHh", icmpHeader
            )
            if type == self.ICMP_RECV and code == self.ICMP_CODE:
                # 返回ICMP数据
                return packet[28:], packetID, sequence, addr
            time_left = time_left - how_long_in_select
            if time_left <= 0:
                return

    def send(self, dest_addr, data, packetID, sequence):
        dest_addr = socket.gethostbyname(dest_addr)
        my_checksum = 0
        header = struct.pack("bbHHh", self.ICMP_SEND, self.ICMP_CODE, my_checksum, packetID, sequence)
        my_checksum = self.checksum(header + data)
        header = struct.pack(
            "bbHHh", self.ICMP_SEND, self.ICMP_CODE, socket.htons(my_checksum), packetID, sequence
        )
        packet = header + data
        self.sock.sendto(packet, (dest_addr, 1))


def _GetSockNum():
    while (True):
        id = random.randint(10000, 32767)
        if (id not in gSOCKETID):
            break
    return id


def _GetMd5(src):
    m = md5.new()
    m.update(src)
    return m.hexdigest()


def _TransData(ss, obj):
    Timeout = 30
    startTime = 0
    data = ''
    while True:
        try:
            if startTime == 0:
                startTime = time.time()
            # 超时
            elif time.time() - startTime > Timeout:
                return 0

            r, w, e = select.select([ss], [], [ss], 0.2)
            if ss in r:
                try:
                    # tcp收数据
                    recv = ss.recv(1024)
                    logger.debug("Server tcp recv {} bytes data".format(len(recv)))
                    if len(recv) > 0:
                        # 向隧道放入数据
                        obj['OutQueue'].put(recv)
                        logger.debug("Server icmp send {} bytes data".format(len(recv)))
                    else:
                        print "Attacker is offline"
                        obj['OutQueue'].put(obj['CloseTCPFlag'])
                        ss.close()
                        return -1
                except Exception as e:
                    print(e), sys._getframe().f_lineno
                    obj['OutQueue'].put(obj['CloseTCPFlag'])
                    return -1

            elif not obj['InQueue'].empty():
                startTime = 0
                while obj['InQueue'].qsize() > 0:
                    recv = obj['InQueue'].get()
                    if recv == obj['CloseTCPFlag']:
                        ss.close()
                        return -1
                    else:
                        data = data + recv
                        logger.debug("server recv icmp {} bytes data".format(len(data)))
                    if obj['CanSend']:
                        if (len(data) > 0):
                            ss.send(data)
                            logger.debug("server send tcp {} bytes data".format(len(recv)))
                        obj['CanSend'] == False
                        data = ''

        except Exception as e:
            print e, sys._getframe().f_lineno
            break


def _ProcessNewClient(obj, addr):
    # 创建TCP套接字
    rs = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    rs.bind(('0.0.0.0', 0))
    rs.listen(10)
    socks = [rs]
    # 随机端口
    ip, sp = rs.getsockname()
    # 向客户端发送0100
    obj['OutQueue'].put("\x01\x00")
    logger.debug("server bind ip: {}, bind port: {}".format(ip, sp))
    # obj['OutQueue'].put("Your server port is :"+str(sp))
    ExitCode = 1
    while ExitCode:
        try:
            r, w, e = select.select(socks, [], socks)
            if rs in r:
                ss, laddr = rs.accept()
                logger.debug("client ip: {} connect".format(laddr[0]))
                # 向客户端发送0000
                obj['OutQueue'].put("\x00\x00")
                # print "Send authenticate info "
            elif e.count > 0:
                break
        except Exception as e:
            print "Tunnel has been closed", e
            break

        print "Now starting translate data..."
        ExitCode = _TransData(ss, obj)

    gSOCKETID.remove(obj['Num'])
    gCLIENTOBJ.remove(obj)
    print "Translate data is over..."


def _ForwardData():
    while True:
        for obj in gCLIENTOBJ:
            if not obj['OutQueue'].empty():
                recv = obj['OutQueue'].get()
                ICMPSOCK.send(obj['Address'], recv, obj['Identifier'], obj['Num'])


def _DataCenter():
    td = threading.Thread(target=_ForwardData)
    td.start()
    while True:
        try:
            # 返回 packet[28:], packetID, sequence, addr
            data, id, seq, addr = ICMPSOCK.recv(1024)
            logger.debug("server recv client data: {}".format(data))
            # 客户端连接,发送过来的data为7个字节，\x01\x01HELLO
            if seq == 0 and data[0:7] == '\x01\x01' + HANDSHAKE:
                # 生成随机端口
                sockNum = _GetSockNum()
                gSOCKETID.append(sockNum)
                obj = {
                    'Num': sockNum,
                    'InQueue': Queue.Queue(),
                    'OutQueue': Queue.Queue(),
                    'Address': addr[0],
                    'Identifier': id,
                    'CanSend': False,
                    'HeartBeatFlag': _GetMd5(str(sockNum) + 'TS'),
                    'CloseTCPFlag': _GetMd5(str(sockNum) + 'TCP')
                }
                # obj['Identifier'] = id
                gCLIENTOBJ.append(obj)
                logger.debug("client bind port: {}, client bind ip: {}".format(sockNum, addr[0]))
                # 处理客户端
                t = threading.Thread(target=_ProcessNewClient, args=(obj, addr[0]))
                t.start()
            elif seq in gSOCKETID:
                for obj in gCLIENTOBJ:
                    if obj['Num'] == seq and obj['Address'] == addr[0]:
                        obj['Identifier'] = id
                        obj['CanSend'] = True
                        if data != obj['HeartBeatFlag']:
                            obj['InQueue'].put(data)
        except Exception as e:
            print e


def _StartServer(lip, Mode):
    global ICMPSOCK
    ICMPSOCK = IcmpSocket(Mode)  # 0 Server Mode
    ICMPSOCK.bind(lip)
    _DataCenter()


if __name__ == '__main__':
    _StartServer('0.0.0.0', 0)