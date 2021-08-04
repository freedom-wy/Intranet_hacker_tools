import socket

# 创建客户端socket
client = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
server_ip = input("请输入服务器IP: ")
server_port = input("请输入服务器PORT: ")
# 连接服务器
client.connect((server_ip, int(server_port)))
print(client.getpeername())
while True:
    msg = input("请输入要发送的消息: ")
    client.send(msg.encode())
    data = client.recv(1024)
    if data.decode() == "EXIT":
        break
    print("服务端发来的数据为: {}".format(data.decode()))
client.close()