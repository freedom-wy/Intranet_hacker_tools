import socketserver


class MyServer(socketserver.BaseRequestHandler):
    def handle(self):
        conn = self.request
        conn.sendall("I am tcp server".encode())
        while True:
            data = conn.recv(1024).decode()
            if data == "exit":
                print("断开与{}的连接".format(self.client_address))
                break
            print("来自{}的客户端发来的消息为: {}".format(self.client_address, data))
            conn.sendall("HELLO CLIENT".encode())


if __name__ == '__main__':
    server = socketserver.ThreadingTCPServer(("0.0.0.0", 9999), MyServer)
    server.serve_forever()
