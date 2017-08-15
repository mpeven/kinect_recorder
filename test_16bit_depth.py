import os
import cv2
import numpy as np
import glob


# Create video
fps = 20.0
dims = (512, 424)
fourcc = cv2.VideoWriter_fourcc(*'x264')
try:
    os.remove('test_vid_d.avi')
except FileNotFoundError:
    pass
vid_d = cv2.VideoWriter('test_vid_d.avi', fourcc, fps, dims)

for idx, f_name in enumerate(glob.glob('depth_images/*')):
    data = cv2.imread(f_name, -1)
    new_data = np.zeros((*data.shape, 3)).astype(np.uint16)
    new_data[:,:,0] = data & 255
    new_data[:,:,1] = data >> 8
    vid_d.write(new_data.astype(np.uint8))

vid_d.release()

# Uncompress video
vidcap = cv2.VideoCapture('test_vid_d.avi')
success, image_data = vidcap.read()
count = 0
success = True
while success:
    image_data = image_data.astype(np.uint16)
    image = (image_data[:,:,1] << 8) + image_data[:,:,0]
    cv2.imwrite("uncompressed_depth/frame%d.png" % count, image)
    success, image_data = vidcap.read()
    count += 1
