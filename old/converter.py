import os
import cv2
import numpy as np
import glob
import logging
logging.basicConfig(level=logging.DEBUG)
from prompter import yesno

# How to test:
#  1 -- Record images and depth-images using kinect
#  2 -- Convert images to compressed video using `images_2_video`
#  3 -- Convert compressed video to images using `video_2_images` (can't on mac)
#  4 -- Compare uncompressed images to the original images

# Run test_script.sh


def images_2_video(image_directory, video_path, ext, codec, depth=False):
    '''
    Compress a directory of images into a video

    Parameters:
        - Image directory
        - Path to save video
        - Whether these are 16 bit depth images
    '''

    if os.path.isfile(video_path):
        if yesno("{} already exists. Overwrite it?".format(video_path)):
            os.remove(video_path)
        else:
            logging.error("Exiting.")

    if not os.path.isdir(image_directory):
        raise FileNotFoundError("No image directory found at {}".format(image_directory))

    all_files = sorted(glob.glob(image_directory + '/*'))
    img = cv2.imread(all_files[0])
    vid = cv2.VideoWriter(filename  = video_path + '.nut',
                          fourcc    = cv2.VideoWriter_fourcc(*codec),#x264
                          fps       = 30.0,
                          frameSize = (img.shape[1], img.shape[0]),
                          isColor   = True)
    # vid2 = cv2.VideoWriter(filename  = video_path + '2.avi',
    #                       fourcc    = cv2.VideoWriter_fourcc(*codec),#x264
    #                       fps       = 30.0,
    #                       frameSize = (img.shape[1], img.shape[0]),
    #                       isColor   = False)

    for idx, f_name in enumerate(all_files):
        # If a 16 bit depth image, put the first 8 bits in the R channel and the
        #   second 8 bits in the G channel
        if depth:
            data = cv2.imread(f_name, -1)
            # new_data = np.zeros((*data.shape, 3)).astype(np.uint16)
            # new_data[:,:,0] = data & 255
            # new_data[:,:,1] = data >> 8
            # vid.write(data.astype(np.uint8))
            vid.write(data.astype(np.uint16))
            # vid1.write((data & 255).astype(np.uint8))
            # vid2.write((data >> 8).astype(np.uint8))
        else:
            data = cv2.imread(f_name)
            vid.write(data.astype(np.uint8))

    vid.release()
    # vid1.release()
    # vid2.release()
    logging.info("Converted {} images into video at {}".format(len(all_files),
                                                               video_path))



def video_2_images(video_path, image_directory, image_extension, depth=False):
    ''' Turn a video into images '''

    if not os.path.isfile(video_path + '.mov'):
        raise FileNotFoundError("No video found at {}".format(video_path))

    if not os.path.isdir(image_directory):
        logging.info("Creating directory {}".format(image_directory))
        os.mkdir(image_directory)

    vidcap = cv2.VideoCapture(video_path + '.mov')
    # vidcap1 = cv2.VideoCapture(video_path + '1.avi')
    # vidcap2 = cv2.VideoCapture(video_path + '2.avi')
    num_frames = vidcap.get(cv2.CAP_PROP_FRAME_COUNT)
    vid_name = os.path.basename(video_path)
    logging.info("Extracting {} frames from {}".format(num_frames, vid_name))
    count = 0
    while True:
        success, image_data = vidcap.read()
        # success, image_data1 = vidcap1.read()
        # success, image_data2 = vidcap2.read()
        if success == False:
            break
        if depth:
            image_data = image_data.astype(np.uint16)
            # image_data1 = image_data1.astype(np.uint16)
            # image_data2 = image_data2.astype(np.uint16)
            image = image_data
            print(image_data)
            exit()
            # image = (image_data[:,:,1] << 8) + image_data[:,:,0]
        else:
            image = cv2.cvtColor(image_data, cv2.COLOR_BGR2GRAY)

        cv2.imwrite("{}/frame{:06d}.{}".format(image_directory, count, image_extension),
                    image)
        count += 1

    vidcap.release()
    # vidcap1.release()
    # vidcap2.release()
    logging.info("Finished - extracted {} frames".format(count))
