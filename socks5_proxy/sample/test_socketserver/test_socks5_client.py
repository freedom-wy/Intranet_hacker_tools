import socket
import socks
import requests

socks.set_default_proxy(socks.SOCKS5, "192.168.28.137", 9999)
socket.socket = socks.socksocket
response = requests.get(url="http://47.112.243.127/", timeout=(5, 5))
print(response.text)