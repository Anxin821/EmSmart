"""
UDP 转发脚本：监听 514 端口，转发到后端 syslog 监听端口（默认 5140）。

用途：H3C 路由器 syslog 固定发往 UDP 514，后端监听 5140 时可用本脚本桥接。
要求：管理员权限运行（Windows 绑定 514 特权端口需要管理员身份）。
"""
import socket

LISTEN_PORT = 514
TARGET_HOST = "127.0.0.1"
TARGET_PORT = 5140

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("0.0.0.0", LISTEN_PORT))
print(f"UDP 转发已启动：0.0.0.0:{LISTEN_PORT} -> {TARGET_HOST}:{TARGET_PORT}")
print("按 Ctrl+C 停止")

while True:
    try:
        data, addr = sock.recvfrom(4096)
        print(f"收到来自 {addr} 的数据包（{len(data)} 字节）")
        forward_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        forward_sock.sendto(data, (TARGET_HOST, TARGET_PORT))
        forward_sock.close()
    except KeyboardInterrupt:
        print("\n转发已停止")
        break
    except Exception as e:
        print(f"转发异常：{e}")