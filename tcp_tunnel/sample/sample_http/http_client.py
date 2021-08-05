# import socket
#
# 首行
# request_line = "GET / HTTP/1.1\r\n"
# 头部
# request_header = "Host: 127.0.0.1\r\n"
# 空行
# request_blank = "\r\n"
# # 拼接Http client 请求数据
# request_data = request_line+request_header+request_blank
#
# client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# client_socket.connect(("192.168.28.137", 80))
# client_socket.send(request_data.encode())
# response = client_socket.recv(2048).decode()
# print(response)
# client_socket.close()

import requests
response = requests.get(url="http://192.168.28.137/")
print(response.text)