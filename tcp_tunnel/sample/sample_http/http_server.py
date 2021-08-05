import socket


# 首行
response_line = "HTTP/1.1 200 OK\r\n"
# 头部
response_header = "Server: apache\r\n"
# 空行
response_blank = "\r\n"
# response数据
response_body = "<h1>hello world</h1>"
# 拼接返回数据
response_data = response_line + response_header + response_blank + response_body

http_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
http_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)
http_server.bind(("0.0.0.0", 80))
http_server.listen(10)
client_conn, client_addr = http_server.accept()
data = client_conn.recv(1024).decode()

request_split = data.split("\r\n")
request_line, request_header = request_split[0], request_split[1]
METHOD, PATH, PROTOCOL = request_line.split(" ")
print(METHOD, PATH, PROTOCOL)

if METHOD == "GET" and PATH == "/":
    client_conn.send(response_data.encode())
    client_conn.close()
http_server.close()
