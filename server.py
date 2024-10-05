# @Time         : 2024/10/5 22:00
# @Author       : Yang Qiang
# @File         : service.py
# @Description  :
import logging
import threading
from concurrent import futures
from operator import index

import grpc

import grpc_service.services_pb2_grpc as s_grpc
import grpc_service.services_pb2 as s
from capture import ImagePub

from detect import DetectImage


class RaspiBerryServer(s_grpc.RPiMessage, DetectImage):
    def __init__(self, object):
        s_grpc.RPiMessage.__init__(self)
        DetectImage.__init__(self, object)

    def GetPosition(self, request, context):
        try:
            print(self.result)
        except:
            pass
        return s.Index(index=2)


def serve(object):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    s_grpc.add_RPiMessageServicer_to_server(object, server)
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
