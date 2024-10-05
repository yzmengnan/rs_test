# @Time         : 2024/10/4 14:04
# @Author       : Yang Qiang
# @File         : detect.py
# @Description  :
import threading
import apriltag

from capture import *

i = ImagePub()

ob1 = ShowImage(i)

i.add_observer(ob1)

thread = threading.Thread(target=i.publish_image_looping)
thread.start()

while True:
    if i.rgb is not None:
        gray = cv2.cvtColor(i.rgb, cv2.COLOR_BGR2GRAY)
        options = apriltag.DetectorOptions(families='tag36h10')
        detector = apriltag.Detector(options)
        results = detector.detect(gray)

        temp = i.rgb
        for r in results:
            # extract the bounding box (x, y)-coordinates for the AprilTag
            # and convert each of the (x, y)-coordinate pairs to integers
            (ptA, ptB, ptC, ptD) = r.corners
            ptB = (int(ptB[0]), int(ptB[1]))
            ptC = (int(ptC[0]), int(ptC[1]))
            ptD = (int(ptD[0]), int(ptD[1]))
            ptA = (int(ptA[0]), int(ptA[1]))

            # draw the bounding box of the AprilTag detection
            cv2.line(temp, ptA, ptB, (0, 255, 0), 2)
            cv2.line(temp, ptB, ptC, (0, 255, 0), 2)
            cv2.line(temp, ptC, ptD, (0, 255, 0), 2)
            cv2.line(temp, ptD, ptA, (0, 255, 0), 2)

            # draw the center (x, y)-coordinates of the AprilTag
            (cX, cY) = (int(r.center[0]), int(r.center[1]))
            cv2.circle(temp, (cX, cY), 5, (0, 0, 255), -1)

            # draw the tag family on the self.rgb
            tagFamily = r.tag_family.decode("utf-8")
            cv2.putText(temp, tagFamily, (ptA[0], ptA[1] - 15),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            print("[INFO] tag family: {}".format(tagFamily))

        # show the output self.rgb after AprilTag detection
        if temp is not None:
            print("show")
            cv2.namedWindow("show", cv2.WINDOW_NORMAL)
            cv2.imshow("show", temp)
            cv2.waitKey(1)
