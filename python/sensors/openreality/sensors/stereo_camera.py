import cv2
import numpy as np
import time
from typing import Tuple
import threading
from enum import Enum

"""
    Camera class allows to capture from shm device
    This is system agnostic and can be used for any hardware
"""
class StereoCamera():
    def __init__(
        self,
        device_left: int, # device, e.g. 0 for /dev/video0
        device_right: int, # device, e.g. 0 for /dev/video0
        resolution: Tuple[int, int],
        crop_area: Tuple[int, int, int, int], # y0,y1,x0,x1
        fps: int = 30
    ):
        # camera parameters
        self._device_left = device_left
        self._device_right = device_right
        self._resolution = resolution
        self._crop_area = crop_area 
        self._fps = fps

        # data
        self._frame: np.ndarray = None
        self._grabbed = False

        # performance
        self._ctime = 0
        self._ptime = 0
        self._real_fps = 0

        # start capture
        self._gst_cmd = (
            # compositor and appsink
            f"nvcompositor name=comp "
            f"sink_0::xpos=0 sink_0::ypos=0 sink_0::width=(int){self._crop_area[3] - self._crop_area[2]} sink_0::height=(int){self._crop_area[1] - self._crop_area[0]} "
            f"sink_1::xpos=(int){self._crop_area[3] - self._crop_area[2]} sink_1::ypos=0 sink_1::width=(int){self._crop_area[3] - self._crop_area[2]} sink_1::height=(int){self._crop_area[1] - self._crop_area[0]} ! "
            f"video/x-raw(memory:NVMM),format=RGBA ! nvvidconv ! video/x-raw,format=BGRx ! videoconvert ! video/x-raw,format=BGR ! appsink max-buffers=1 drop=True "
            # camera left
            f"nvarguscamerasrc sensor-id={self._device_left} ! "
            f"video/x-raw(memory:NVMM), width=(int){self._resolution[0]}, height=(int){self._resolution[1]}, "
            f"format=(string)NV12, framerate=(fraction){self._fps}/1 ! "
            f"nvvidconv flip-method=0 top=(int){self._crop_area[0]} bottom=(int){self._crop_area[1]} left=(int){self._crop_area[2]} right=(int){self._crop_area[3]} ! "
            f"video/x-raw(memory:NVMM),width=(int){self._crop_area[3] - self._crop_area[2]},height=(int){self._crop_area[1] - self._crop_area[0]}, format=RGBA ! comp.sink_0 "
            # camera right
            f"nvarguscamerasrc sensor-id={self._device_right} ! "
            f"video/x-raw(memory:NVMM), width=(int){self._resolution[0]}, height=(int){self._resolution[1]}, "
            f"format=(string)NV12, framerate=(fraction){self._fps}/1 ! "
            f"nvvidconv flip-method=0 top=(int){self._crop_area[0]} bottom=(int){self._crop_area[1]} left=(int){self._crop_area[2]} right=(int){self._crop_area[3]} ! "
            f"video/x-raw(memory:NVMM),width=(int){self._crop_area[3] - self._crop_area[2]},height=(int){self._crop_area[1] - self._crop_area[0]}, format=RGBA ! comp.sink_1 "
        )
        print(self._gst_cmd)
        self._cap = cv2.VideoCapture(self._gst_cmd, cv2.CAP_GSTREAMER)

    @property
    def opened(self):
        return self._cap.isOpened()

    @property
    def frame_ready(self):
        return self._cap.grab()

    @property
    def cap(self):
        return self._cap

    @property
    def frame_ok(self):
        return self._grabbed

    @property
    def resolution(self):
        return self._resolution

    @property
    def fps(self):
        return self._real_fps

    @property
    def frame(self):
        # get frame
        self._grabbed, self._frame = self._cap.retrieve(0)

        # calculate fps
        self._ctime = time.time()
        self._real_fps = 1/(self._ctime-self._ptime)
        self._ptime = self._ctime
        return self._frame

    @property
    def shape(self):
        return self._frame.shape

    @property
    def size(self):
        return self._frame.nbytes

# demo code to run this separately
def main():
    # camera setup
    crop_area = (204,1644,992,2272) # y0,y1,x0,x1
    # TODO: make this a configuration
    camera_mode = (3264,1848,28)
    cam_left = StereoCamera(
        device_left=0,
        device_right=1,
        resolution=(camera_mode[0], camera_mode[1]),
        crop_area=crop_area,
        fps=camera_mode[2]
    )

    # window
    #cv2.namedWindow("render", cv2.WINDOW_NORMAL)
    #cv2.setWindowProperty("render", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    # capture
    while cam_left.opened:
        # get frame
        if cam_left.frame_ready:
            # get frame
            frame = cam_left.frame
            print(frame.shape)
            #cv2.imshow("render", frame)    
            # show fps
            print(cam_left.fps)

        # break if necessary
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cam_left.cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()