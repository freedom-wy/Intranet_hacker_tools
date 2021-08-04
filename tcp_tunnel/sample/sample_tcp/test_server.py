import socket
import threading


def handle_new_client(s):
    while True:
        # 收取客户端发来的数据
        data = s.recv(1024)
        print("客户端发来的数据为: {}".format(data.decode()))
        if data.decode() == "EXIT":
            s.close()
            break
        msg = input("请输入要发送的数据: ")
        s.send(msg.encode())


def create_server():
    # 创建连接
    server = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
    # 绑定IP和端口
    server.bind(("0.0.0.0", 0))
    # 返回绑定的IP和随机端口号
    ip, port = server.getsockname()
    print("服务端已启动，IP地址为: {}, PORT为: {}".format(ip, port))
    # 设置最大连接数
    server.listen(128)
    while True:
        # 客户端连接
        try:
            new_client, client_address = server.accept()
        except:
            server.close()
            break
        else:
            print("有新客户端连接,客户端IP为: {}".format(client_address[0]))
            t = threading.Thread(target=handle_new_client, args=(new_client,))
            t.start()
    print("服务端线程")


if __name__ == '__main__':
    create_server()
    print("主进程")
