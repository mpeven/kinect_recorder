import cv2
import numpy as np

vidcap = cv2.VideoCapture('test.avi')
success, image = vidcap.read(-1)
count = 0
success = True
while success:
    # image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    print(image)
    exit()
    cv2.imwrite("uncompressed_depth/frame%d.png" % count, image)
    success,image = vidcap.read(-1)
    count += 1

