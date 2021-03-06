#!/usr/bin/env python
# coding=utf-8

"""
filename: rtcp.py
@desc:
利用 Python 的 socket 端口转发，用于远程维护
如果连接不到远程，会 sleep 36s，最多尝试 200（即两小时）

@usage:
./rtcp.py stream1 stream2
stream 为：l:port 或 c:host:port
l:port 表示监听指定的本地端口
c:host:port 表示监听远程指定的端口

@author: watercloud, zd, knownsec team
@web: www.knownsec.com, blog.knownsec.com
@date: 2009-7
"""

import socket
import sys
import threading
import time
from handle_log import logger

streams = [None, None]  # 存放需要进行数据转发的两个数据流（都是 SocketObj 对象）
debug = 1  # 调试状态 0 or 1


def _usage():
    print('Usage: ./rtcp.py stream1 stream2\nstream: l:port  or c:host:port')


def _get_another_stream(num):
    """
    从streams获取另外一个流对象，如果当前为空，则等待
    """
    logger.debug("change socket")
    # 10001的 0, 10002的1
    if num == 0:
        num = 1
    elif num == 1:
        num = 0
    # else:
    #     raise Exception('ERROR')

    while True:
        if streams[num] == 'quit':
            logger.debug('can not connect to the target, quit now!')
            sys.exit(1)

        if streams[num] is not None:
            return streams[num]
        elif streams[num] is None and streams[num ^ 1] is None:
            logger.debug('stream CLOSED')
            return None
        else:
            time.sleep(1)


def _xstream(num, s1, s2, name):
    """
    交换两个流的数据
    num为当前流编号,主要用于调试目的，区分两个回路状态用。
    """
    s1_info = None
    s2_info = None
    try:
        while True:
            if name == "server":
                s1_info = s1.getsockname()
                s2_info = s2.getsockname()
            elif name == "client":
                s1_info = s1.getpeername()
                s2_info = s2.getpeername()
            # 注意，recv 函数会阻塞，直到对端完全关闭（close 后还需要一定时间才能关闭，最快关闭方法是 shutdow）
            buff = s1.recv(1024)
            logger.debug("{} {}:{} recv {} bytes data".format(name, s1_info[0], s1_info[1], len(buff)))
            # if debug > 0:
            #     print('%d recv' % num)
            if len(buff) == 0:  # 对端关闭连接，读不到数据
                logger.debug('%d one closed' % num)
                break
            s2.sendall(buff)
            logger.debug("{} {}:{} send {} bytes data".format(name, s2_info[0], s2_info[1], len(buff)))
            # if debug > 0:
            #     print('%d sendall' % num)
    except:
        logger.error('%d one connect closed.' % num)

    try:
        s1.shutdown(socket.SHUT_RDWR)
        s1.close()
    except:
        pass

    try:
        s2.shutdown(socket.SHUT_RDWR)
        s2.close()
    except:
        pass

    streams[0] = None
    streams[1] = None
    logger.debug('%d CLOSED' % num)


def _server(port, num):
    """
    处理服务情况，num 为流编号（第 0 号还是第 1 号）
    """
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(('0.0.0.0', port))
    logger.debug("start server, bind port: {}".format(port))
    srv.listen(10)
    while True:
        # 客户端连接
        conn, addr = srv.accept()
        # print('connected from: %s' % str(addr[0]))
        server_info = srv.getsockname()
        logger.debug("connect from {}, connect to {}:{}".format(addr[0], server_info[0], server_info[1]))
        # streams[0] = 10001的client连接
        # streams[1] = 10002的client连接
        streams[num] = conn  # 放入本端流对象
        s2 = _get_another_stream(num)  # 获取另一端流对象
        _xstream(num, conn, s2, "server")


def _connect(host, port, num):
    """处理连接，num 为流编号（第 0 号还是第 1 号）

    @note: 如果连接不到远程，会 sleep 36s，最多尝试 200（即两小时）
    """
    not_connet_time = 0
    wait_time = 36
    try_cnt = 199
    while True:
        if not_connet_time > try_cnt:
            streams[num] = 'quit'
            logger.debug('not connected')
            return None

        # 创建socket客户端
        conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            # 127.0.0.1:22, 222.2.2.2:10001
            conn.connect((host, port))
        except Exception:
            logger.error('can not connect %s:%s!' % (host, port))
            not_connet_time += 1
            time.sleep(wait_time)
            continue

        logger.debug('connected to %s:%i' % (host, port))
        streams[num] = conn  # 放入本端流对象
        s2 = _get_another_stream(num)  # 获取另一端流对象
        # conn为当前连接，s2为另一个端口连接
        _xstream(num, conn, s2, "client")


def main():
    if len(sys.argv) != 3:
        _usage()
        sys.exit(1)
    tlist = []  # 线程列表，最终存放两个线程对象
    targv = [sys.argv[1], sys.argv[2]]
    for i in [0, 1]:
        s = targv[i]  # stream 描述 c:ip:port 或 l:port
        sl = s.split(':')
        # 服务端
        if len(sl) == 2 and (sl[0] == 'l' or sl[0] == 'L'):  # l:port
            # ./rtcp.py l:10001 l:10002
            t = threading.Thread(target=_server, args=(int(sl[1]), i))
            tlist.append(t)
        # 客户端
        elif len(sl) == 3 and (sl[0] == 'c' or sl[0] == 'C'):  # c:host:port
            # ./rtcp.py c:127.0.0.1:22 c:222.2.2.2:10001
            t = threading.Thread(target=_connect, args=(sl[1], int(sl[2]), i))
            tlist.append(t)
        else:
            _usage()
            sys.exit(1)

    for t in tlist:
        t.start()
    for t in tlist:
        t.join()
    sys.exit(0)


if __name__ == '__main__':
    main()
