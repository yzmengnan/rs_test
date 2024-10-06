# @Time         : 2024/10/5 22:05
# @Author       : Yang Qiang
# @File         : client.py
# @Description  :

import time
from time import sleep

import grpc

import grpc_service.services_pb2 as s
import grpc_service.services_pb2_grpc as s_grpc
import keyboard

channel = grpc.insecure_channel('localhost:50051')

stub = s_grpc.RPiMessageStub(channel)

s = s.Positions(p1=0.2, j1=0.2, j2=0.2,
                j3=0.2, j4=0.2, j5=0.2, j6=0.2)

while True:
    # sleep(0.5)
    if keyboard.is_pressed('s'):
        print("send")
        stub.GetPosition(s).index
        sleep(0.5)
