# @Time         : 2024/10/5 22:05
# @Author       : Yang Qiang
# @File         : client.py
# @Description  :
import struct
import sys
import threading
import time
from time import sleep

import grpc

import grpc_service.services_pb2 as s
import grpc_service.services_pb2_grpc as s_grpc
import keyboard

channel = grpc.insecure_channel('raspberrypi:50051')

stub = s_grpc.RPiMessageStub(channel)

# s = s.Positions(p1=0.2, j1=0.2, j2=0.2,
#                 j3=0.2, j4=0.2, j5=0.2, j6=0.2)

import socket

server_address = ('remote-rcs', 10002)

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

joints = (0,)*7


def socket_net():
    global joints
    sock.connect(server_address)
    while True:
        data = sock.recv(132)
        if len(data) != 132:
            print("data received invalid")
            continue

        start_index = 8
        float_data = data[start_index:start_index + 4 * 7]
        joints = struct.unpack('7f', float_data)
        # print(joints)


thread = threading.Thread(target=socket_net)
thread.start()

# while True:
#     sleep(1)

while True:
    sleep(0.05)
    if keyboard.is_pressed('s'):
        print("send")
        if len(joints) != 7:
            continue
        else:
            send_ = s.Positions(p1=joints[6], j1=joints[0], j2=joints[1], j3=joints[2], j4=joints[3], j5=joints[4],
                                j6=joints[5])
            var = stub.GetPosition(send_).index
            print(f"send finish! returned:{var}")
        sleep(0.1)
    elif keyboard.is_pressed('q'):
        print("quit")
        sys.exit(0)
