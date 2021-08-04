import socket
import time
import threading
from handle_log import logger
from traceback import format_exc

# 端口映射配置信息
CFG_LOCAL_IP = '0.0.0.0'
CFG_LOCAL_PORT = 10086

# 接收数据缓存大小
PKT_BUFF_SIZE = 2048


# 单向流数据传递
def tcp_mapping_worker(conn_receiver, conn_sender, thread_name):
    while True:
        try:
            # local_conn从应用发来的数据, remote_conn收到远端发来的数据
            data = conn_receiver.recv(PKT_BUFF_SIZE)
            logger.debug("数据为: {}".format(data))
        except Exception as e:
            logger.debug(thread_name)
            logger.debug(format_exc())
            conn_receiver.close()
            break
        if not data:
            logger.info('No more data is received.')
            pass
            # 无数据传输
            # conn_receiver.close()
            # conn_sender.close()
            # break
        try:
            # 从remote_conn发出去, local_conn发到应用
            conn_sender.sendall(data)
        except Exception:
            logger.debug(thread_name)
            logger.debug(format_exc())
            conn_sender.close()
            break
        logger.info(
            'Mapping > %s -> %s > %d bytes, thread name is %s.' % (conn_receiver.getpeername(), conn_sender.getpeername(), len(data), thread_name))
    return


# 端口映射请求处理
def tcp_mapping_request(local_conn, remote_ip, remote_port):
    remote_conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # remote_conn.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, True)
    # remote_conn.ioctl(socket.SIO_KEEPALIVE_VALS, (1, 60*1000, 30*1000))
    try:
        # 连接远端服务器
        remote_conn.connect((remote_ip, remote_port))
    except Exception as e:
        local_conn.close()
        # logger.error('Unable to connect to the remote server.')
        logger.debug(format_exc())
        return

    threading.Thread(target=tcp_mapping_worker, args=(local_conn, remote_conn, "local_remote")).start()
    threading.Thread(target=tcp_mapping_worker, args=(remote_conn, local_conn, "remote_local")).start()


# 端口映射函数
def tcp_mapping(remote_ip, remote_port, local_ip, local_port):
    local_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    local_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    local_server.bind((local_ip, local_port))
    logger.debug("绑定本地IP: {}, PORT: {}".format(local_ip, local_port))
    local_server.listen(5)

    while True:
        try:
            # 返回客户端连接信息
            (local_conn, local_addr) = local_server.accept()
            logger.debug("客户端连接信息: {}:{}".format(local_addr[0], local_addr[1]))
        except Exception as e:
            local_server.close()
            logger.debug('Stop mapping service.')
            break
        else:
            threading.Thread(target=tcp_mapping_request, args=(local_conn, remote_ip, remote_port)).start()


# 主函数
if __name__ == '__main__':
    # CFG_REMOTE_IP = input("请输入要连接的服务端IP: ")
    # CFG_REMOTE_PORT = input("请输入要连接的PORT: ")
    CFG_REMOTE_IP = "47.98.165.107"
    CFG_REMOTE_PORT = "9001"
    tcp_mapping(CFG_REMOTE_IP.strip(), int(CFG_REMOTE_PORT.strip()), CFG_LOCAL_IP, CFG_LOCAL_PORT)
