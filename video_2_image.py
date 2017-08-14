import cv2
import numpy as np

vidcap = cv2.VideoCapture('raw_vid_depth.avi')
success, image = vidcap.read()
count = 0
success = True
while success:
    image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    cv2.imwrite("uncompressed_depth/frame%d.png" % count, image.astype(np.uint8))
    success,image = vidcap.read()
    count += 1

