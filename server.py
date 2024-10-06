# @Time         : 2024/10/5 22:00
# @Author       : Yang Qiang
# @File         : service.py
# @Description  :
import logging
import os
import threading
from concurrent import futures

import cv2
import grpc

import grpc_service.services_pb2_grpc as s_grpc
import grpc_service.services_pb2 as s
from capture import ImagePub

from detect import DetectImage


class RaspiBerryServer(s_grpc.RPiMessage, DetectImage):
    def __init__(self, Object):
        s_grpc.RPiMessage.__init__(self)
        DetectImage.__init__(self, Object)
        self.cnt = 0

    def GetPosition(self, request, context):
        try:
            os.mkdir('./img_files')
        except FileExistsError:
            pass
        # if len(self.result) != 0:
        #     print(self.result[0].pose_t)
        cv2.imwrite(f"./img_files/"
                    f"{self.cnt}-{request.p1}-{request.j1}"
                    f"-{request.j2}-{request.j3}-{request.j4}"
                    f"-{request.j5}-{request.j6}.jpg", self.subject.rgb)
        self.cnt = self.cnt + 1
        return s.Index(index=2)


def serve(Object):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    s_grpc.add_RPiMessageServicer_to_server(Object, server)
    server.add_insecure_port('[::]:50051')
    server.start()
    server.wait_for_termination()


if __name__ == "__main__":
    i = ImagePub()
    r = RaspiBerryServer(i)
    i.add_observer(r)
    threading.Thread(target=i.publish_image_looping).start()
    logging.basicConfig()
    serve(r)
