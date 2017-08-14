import freenect
import cv2
import numpy as np

cv2.namedWindow('Depth')
cv2.namedWindow('RGB')
keep_running = True


def display_depth(dev, data, timestamp):
    global keep_running
    cv2.imshow('Depth', data.astype(np.uint8))
    if cv2.waitKey(10) == 27:
        keep_running = False


def display_rgb(dev, data, timestamp):
    print("{}".format(timestamp))
    global keep_running
    cv2.imshow('RGB', cv2.cvtColor(data, cv2.COLOR_RGB2BGR))
    if cv2.waitKey(10) == 27:
        keep_running = False


def body(*args):
    if not keep_running:
        raise freenect.Kill


print('Press ESC in window to stop')
freenect.runloop(depth=display_depth,
                 video=display_rgb,
                 body=body)
