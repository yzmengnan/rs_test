# @Time         : 2024/10/4 14:04
# @Author       : Yang Qiang
# @File         : detect.py
# @Description  :
import threading

from capture import *
import pupil_apriltags as apriltag

i = ImagePub()

ob1 = ShowImage(i)

i.add_observer(ob1)

thread = threading.Thread(target=i.publish_image_looping)
thread.start()

profile = i.camera.profile.get_stream(rs.stream.depth)

intr = profile.as_video_stream_profile().get_intrinsics()


print(intr)

at_detector = apriltag.Detector(
    families="tag36h11",
    nthreads=1,
    quad_decimate=1.0,
    quad_sigma=0.0,
    refine_edges=1,
    decode_sharpening=0.25,
    debug=0
)
while True:
    img = i.rgb
    if img is not None:
        temp = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        result = at_detector.detect(temp, estimate_tag_pose=True, camera_params=(intr.fx, intr.fy, intr.ppx, intr.ppy), tag_size=0.1)
        print(result)
    sleep(0.05)
