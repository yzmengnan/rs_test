# @Time         : 2024/9/30 15:39
# @Author       : Yang Qiang
# @File         : capture.py
# @Description  :
import argparse
import datetime
import json
import os
import threading
from time import sleep

import cv2
import numpy as np
import pyrealsense2 as rs



#
# def get_aligned_images(dirname, aligned_frames, depth_scale, profile):
#     aligned_depth_frame = aligned_frames.get_depth_frame()
#     color_frame = aligned_frames.get_color_frame()
#     intr = color_frame.profile.as_video_stream_profile().intrinsics
#     camera_parameters = {'fx': intr.fx, 'fy': intr.fy,
#                          'ppx': intr.ppx, 'ppy': intr.ppy,
#                          'height': intr.height, 'width': intr.width,
#                          'depth_scale': profile.get_device().first_depth_sensor().get_depth_scale()
#                          }
#     # with open(os.path.join(dirname, 'intrinsics.json'), 'w') as fp:
#     #     json.dump(camera_parameters, fp)
#     color_image = np.asanyarray(color_frame.get_data(), dtype=np.uint8)
#     depth_image = np.asanyarray(aligned_depth_frame.get_data(), dtype=np.float32)
#     mi_d = np.min(depth_image[depth_image > 0])
#     ma_d = np.max(depth_image)
#     depth = (255 * (depth_image - mi_d) / (ma_d - mi_d + 1e-8)).astype(np.uint8)
#     depth_image_color = cv2.applyColorMap(depth, cv2.COLORMAP_JET)
#     depth_image = np.asanyarray(aligned_depth_frame.get_data(), dtype=np.float32) * depth_scale * 1000
#     return color_image, depth_image, depth_image_color
#

def get_aligned_images(aligned_frames, depth_scale, profile):
    aligned_depth_frame = aligned_frames.get_depth_frame()
    color_frame = aligned_frames.get_color_frame()
    intr = color_frame.profile.as_video_stream_profile().intrinsics
    camera_parameters = {'fx': intr.fx, 'fy': intr.fy,
                         'ppx': intr.ppx, 'ppy': intr.ppy,
                         'height': intr.height, 'width': intr.width,
                         'depth_scale': profile.get_device().first_depth_sensor().get_depth_scale()
                         }
    color_image = np.asanyarray(color_frame.get_data(), dtype=np.uint8)
    depth_image = np.asanyarray(aligned_depth_frame.get_data(), dtype=np.float32)
    mi_d = np.min(depth_image[depth_image > 0])
    ma_d = np.max(depth_image)
    depth = (255 * (depth_image - mi_d) / (ma_d - mi_d + 1e-8)).astype(np.uint8)
    depth_image_color = cv2.applyColorMap(depth, cv2.COLORMAP_JET)
    depth_image = np.asanyarray(aligned_depth_frame.get_data(), dtype=np.float32) * depth_scale * 1000
    return color_image, depth_image, depth_image_color


def parse_opt():
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", type=str, default='', help="images save path")
    parser.add_argument("--mode", type=int, default=0, help="0(auto) or 1(manual)")
    parser.add_argument("--image_format", type=int, default=0, help="option: 0->jpg 1->png")
    parser.add_argument("--image_width", type=int, default=1280, help="width of the image, recommended 1280 or 640")
    parser.add_argument("--image_height", type=int, default=720, help="height of the image, recommended 720 or 480")
    parser.add_argument("--fps", type=int, default=30, help="frame rate of shooting")
    opt = parser.parse_args()
    return opt


class CameraObject:
    def __init__(self, opt):
        self.pipline = rs.pipeline()
        self.config = rs.config()
        self.config.enable_stream(rs.stream.color, opt.image_width, opt.image_height, rs.format.bgr8, opt.fps)
        self.config.enable_stream(rs.stream.depth, opt.image_width, opt.image_height, rs.format.z16, opt.fps)
        self.profile = self.pipline.start(self.config)
        align_to = rs.stream.color
        self.align = rs.align(align_to)

    def get_pipline(self):
        return self.pipline

    def get_align(self):
        return self.align

    def get_depth_sensor(self):
        return self.profile.get_device().first_depth_sensor()

    def get_depth_scale(self):
        return self.get_depth_sensor().get_depth_scale()

    def get_profile(self):
        return self.profile


class CameraOperation:
    def __init__(self, cam: CameraObject):
        self.camera = cam

    def grab_image(self):
        pipline = self.camera.get_pipline()
        frames = pipline.wait_for_frames()
        aligned_frames = self.camera.align.process(frames)
        depth_sensor = self.camera.get_depth_sensor()
        depth_scale = self.camera.get_depth_scale()
        rgb, depth, depth_rgb = get_aligned_images(aligned_frames, depth_scale, self.camera.get_profile())
        return rgb, depth, depth_rgb


class Subject(CameraOperation):
    def __init__(self, cam: CameraObject):
        super().__init__(cam)
        self._observers = []
        self.rgb = None
        self.depth = None
        self.depth_rgb = None

    def add_observer(self, observer):
        self._observers.append(observer)

    def remove_observer(self, observer):
        self._observers.remove(observer)

    def notify_observer(self):
        for observer in self._observers:
            self.rgb, self.depth, self.depth_rgb = self.grab_image()
            observer.notify()


class Observer:
    def notify(self):
        raise NotImplementedError("Subclass must implement notify")


class ShowImage(Observer):
    def __init__(self, subject):
        self.running = True
        self.subject = subject
        self.showThread = None

    def __loop(self):
        while True:
            if self.running:
                try:
                    cv2.namedWindow('image', cv2.WINDOW_GUI_NORMAL | cv2.WINDOW_FREERATIO)
                    cv2.imshow('image', self.subject.rgb)
                    cv2.waitKey(1)
                    # if cv2.waitKey(1) & 0xFF == ord('q'):
                    #     cv2.destroyAllWindows()
                    #     self.running = False
                    #     break
                except:
                    sleep(0.5)
            else:
                break

    def stop_looping(self):
        self.running = False
        cv2.destroyAllWindows()

    def restart_looping(self):
        self.running = True

    def notify(self):
        if self.showThread is None or not self.showThread.is_alive():
            self.showThread = threading.Thread(target=self.__loop)
            self.showThread.start()
            # print("start show thread")


class ImagePub(Subject):
    def __init__(self):
        self.opt = parse_opt()
        camera = CameraObject(self.opt)
        super().__init__(camera)

    def publish_image_looping(self):
        while True:
            self.notify_observer()
            sleep(0.01)


class Capture:
    def __init__(self, opt: argparse.ArgumentParser):
        self.opt = opt
        self.rgb, self.depth, self.depth_rgb = None, None, None
        self.isShowing = False
        self.showThread = None
        self.isGrabbing = False
        self.grabThread = None
        self.pipline = rs.pipeline()
        self.config = rs.config()
        self.config.enable_stream(rs.stream.color, opt.image_width, opt.image_height, rs.format.bgr8, opt.fps)
        self.config.enable_stream(rs.stream.depth, opt.image_width, opt.image_height, rs.format.z16, opt.fps)
        self.profile = self.pipline.start(self.config)
        self.depth_sensor = self.profile.get_device().first_depth_sensor()
        self.depth_scale = self.depth_sensor.get_depth_scale()
        self.image_formats = ['.jpg', '.png']
        align_to = rs.stream.color
        self.align = rs.align(align_to)
        self.n = None
        now = datetime.datetime.now()
        if os.path.exists(os.path.join(opt.path, 'images')):
            dir_name = opt.path
            if len(os.listdir(os.path.join(opt.path, 'images'))):
                li = sorted(os.listdir(os.path.join(opt.path, 'images')), key=lambda x: eval(x.split('.')[0]))
                self.n = eval(li[-1].split('.')[0])
            else:
                self.n = 0

        elif opt.path == '':
            self.n = 0
            dir_name = os.path.join(opt.path, now.strftime("%Y_%m_%d_%H_%M_%S"))
        else:
            self.n = 0
            dir_name = os.path.join(opt.path)

        self.dir_name = dir_name
        self.color_dir = os.path.join(dir_name, 'images')
        self.depth_dir = os.path.join(dir_name, 'DepthImages')
        self.depth_color_dir = os.path.join(dir_name, 'DepthColorImages')
        self.depth_npy_dir = os.path.join(dir_name, 'DepthNpy')

    def make_dir(self):
        if not os.path.exists(self.dir_name):
            os.mkdir(self.dir_name)
            os.mkdir(self.color_dir)
            os.mkdir(self.depth_dir)
            os.mkdir(self.depth_color_dir)
            os.mkdir(self.depth_npy_dir)

    def start_show(self):
        if self.showThread is None or not self.showTahread.is_alive():
            self.isShowing = True
            self.showThread = threading.Thread(target=self.__show)
            self.showThread.start()

    def start_grab(self):
        if self.grabThread is None or not self.grabTahread.is_alive():
            self.isGrabbing = True
            self.grabThread = threading.Thread(target=self.__grab)
            self.grabThread.start()

    def stop_grab(self):
        self.isGrabbing = False

    def __show(self):
        while self.isShowing:
            try:
                cv2.imshow('RGB image', self.rgb)
                key = cv2.waitKey(1)
                if key & 0xFF == ord('q'):
                    self.isShowing = False
                    cv2.destroyAllWindows()
            except Exception as e:
                pass

    def __grab(self):
        while self.isGrabbing:
            self.frames = self.pipline.wait_for_frames()
            self.aligned_frames = self.align.process(self.frames)
            try:
                self.rgb, self.depth, self.depth_rgb = get_aligned_images(self.dir_name, self.aligned_frames, self.depth_scale, self.profile)
            except:
                pass

        self.pipline.stop()

    def save_img(self):
        try:
            self.make_dir()
            if self.isGrabbing:
                cv2.imwrite(os.path.join(self.color_dir, str(self.n) + self.image_formats[self.opt.image_format]), self.rgb)
                cv2.imwrite(os.path.join(self.depth_dir, str(self.n) + self.image_formats[self.opt.image_format]), self.depth)
                cv2.imwrite(os.path.join(self.depth_color_dir, str(self.n) + self.image_formats[self.opt.image_format]), self.depth_rgb)
                np.save(os.path.join(self.depth_npy_dir, str(self.n)), self.depth)
                print('{}{} is saved!'.format(self.n, self.image_formats[self.opt.image_format]))
                self.n = self.n + 1
        except Exception as e:
            pass
