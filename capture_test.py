# @Time         : 2024/9/30 17:47
# @Author       : Yang Qiang
# @File         : capture_test.py
# @Description  :

from capture import *

if __name__ == '__main__':

    i = ImagePub()
    ob1 = ShowImage(i)
    i.add_observer(ob1)

    thread = threading.Thread(target=i.publish_image_looping)
    thread.start()

    while True:
        sleep(0.1)
        ob1.restart_looping()
