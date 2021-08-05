import socket
import struct
import select

address = ""
port = 0


def IsAvailable(connection, NMETHODS):
    methods = []
    for i in range(NMETHODS):
        data = connection.recv((1))
        print(data)
        methods.append(ord(data))
    return methods


def ExchangeData(client, remote):
    while True:
        # 等待数据
        rs, ws, es = select.select([client, remote], [], [])
        if client in rs:
            data = client.recv(4096)
            if remote.send(data) <= 0:
                break
        if remote in rs:
            data = remote.recv(4096)
            if client.send(data) <= 0:
                break


def handle_server():
    global address, port
    server = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("0.0.0.0", 9999))
    server.listen(10)
    new_client, client_address = server.accept()
    # 收取客户端的认证请求
    data1 = new_client.recv(2)
    # 从客户端读取并解包两个字节数据
    # 5, 1
    VER, NMETHODS = struct.unpack("!BB", data1)

    if int(VER) == 5:
        methods = IsAvailable(new_client, NMETHODS)
        if 0 not in set(methods):
            print("认证方法不支持")
            new_client.close()
            server.close()
            return
        else:
            # 服务端回复
            new_client.sendall(struct.pack("!BB", 5, 0))
            # 客户端连接请求,连接远端网络
            version, cmd, _, address_type = struct.unpack("!BBBB", new_client.recv(4))
            if int(version) == 5:
                # ipv4
                if address_type == 1:
                    address = socket.inet_ntoa(new_client.recv(4))
                # domain
                elif address_type == 3:
                    domain_length = ord(str(new_client.recv(1)[0]))
                    address = new_client.recv(domain_length)
                port = struct.unpack("!H", new_client.recv(2))[0]
            # 服务端回应连接
            # connect
            if cmd == 1:
                remote = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                remote.connect((address, port))
                print("已建立连接{}:{}".format(address, port))
                bind_address = remote.getsockname()
                addr = struct.unpack("!I", socket.inet_aton(bind_address[0]))[0]
                port = bind_address[1]
                reply = struct.pack("!BBBBIH", 5, 0, 0, address_type, addr, port)
                new_client.sendall(reply)
                if reply[1] == 0 and cmd == 1:
                    ExchangeData(new_client, remote)

    else:
        print("版本不支持")
        return


if __name__ == '__main__':
    handle_server()
