import sys
sys.path.append('/home/mpeven1/src/py-faster-rcnn/tools')
import _init_paths
from fast_rcnn.config import cfg
from fast_rcnn.test import im_detect
from fast_rcnn.nms_wrapper import nms

import os, sys # sys stuff
import argparse # for commandline args
import glob # file i/o
import scipy.io as sio # Matlab file i/o
import numpy as np
import time # timing detector and tracker
import caffe, cv2 # computer vision
from PIL import Image, ImageFilter
from subprocess import call
from StringIO import StringIO
import pickle
from tqdm import tqdm

CLASSES = ('__background__','Torso','Head','Left Arm','Right Arm','Leg')

RAMBO_MOUNT_POINT = '/home/mpeven1/rambo'
BASE_PATH = RAMBO_MOUNT_POINT + "/edata/WICU_DATASET_2014/untar/WICU-room5_"
prototxt = RAMBO_MOUNT_POINT + '/home/mpeven/detector_tracker/test.prototxt'
caffemodel = RAMBO_MOUNT_POINT + '/home/mpeven/detector_tracker/vgg_cnn_m_1024_faster_rcnn_peopledetection_iter_70000.caffemodel'
detector_out_dir = RAMBO_MOUNT_POINT + '/edata/WICU_DATASET_2014/detector_output/'
detector_example_dir = RAMBO_MOUNT_POINT + '/edata/WICU_DATASET_2014/detector_output/test_imgs/'
KEY_FILE = RAMBO_MOUNT_POINT + "/edata/WICU_DATASET_2014/demoTracking/key.bin"
KEY = np.fromfile(KEY_FILE, dtype=np.int8)



def main():
    #Get the images
    rgb_images, images_id = get_images()
    print(images_id)
    print len(rgb_images)
    print rgb_images[:5]

    #Run the py-faster-rcnn detector
    print("Starting detector")
    time_start = time.time()
    detections = detect(rgb_images)
    time_diff = time.time() - time_start
    print("Detection took {:.1f}s for {:d} images".format(time_diff, len(rgb_images)))

    #Visualize detections
    print("Visualizing detections")
    time_start = time.time()
    visualize_detections(rgb_images, detections)
    time_diff = time.time() - time_start
    print("Creating detections video took {:.1f}s to create".format(time_diff))

    #Save the detections
    det_out_file = os.path.join(detector_out_dir, '{}.detections'.format(images_id))
    pickle.dump(detections, open(det_out_file, 'w'))



def main_auto():
    rgb_imags, images_id = get_images()
    print("Detecting on {}".format(images_id))
    detections = detect(rgb_images)
    det_out_file = os.path.join(detector_out_dir, '{}.detections'.format(images_id))
    pickle.dump(detections, open(det_out_file, 'w'))




def detect(rgb_images):
    '''
    Runs the py-faster-rcnn detector over the images passed in as the argument.
    Outputs results to the defined results file
    '''
    cfg.TEST.HAS_RPN = True
    caffe.set_mode_gpu()
    caffe.set_device(0)
    cfg.GPU_ID = 0

    with suppress_stdout_stderr():
        net = caffe.Net(prototxt, caffemodel, caffe.TEST)

    # Warmup on a dummy image
    im = 128 * np.ones((480, 640, 3), dtype=np.uint8)
    for i in xrange(2):
        _, _= im_detect(net, im)

    # Save detections in a list
    detections = []
    for image_index, image in tqdm(enumerate(rgb_images)):
        im = decrypt_image(image)
        scores, boxes = im_detect(net, im)
        CONF_THRESH = 0.68
        NMS_THRESH = 0.3
        for class_index, body_part_class in enumerate(CLASSES[1:]):
            class_index += 1 # skip background
            cls_boxes = boxes[:, 4*class_index:4*(class_index + 1)]
            cls_scores = scores[:, class_index]
            dets = np.hstack((cls_boxes,
                              cls_scores[:, np.newaxis])).astype(np.float32)
            keep = nms(dets, NMS_THRESH) # Combines overlapping bboxes?
            dets = dets[keep, :]
            inds = np.where(dets[:, -1] >= CONF_THRESH)[0]
            for i in inds:
                bbox = [dets[i,0]+1, dets[i,1]+1, dets[i,2]+1, dets[i,3]+1]
                if class_index == 1:    # Head (put as bpart2)
                    detections.append({'frame':image_index+1, 'bpart':2,
                                       'name': 'Head',
                                       'score':dets[i,-1], 'bbox':bbox})
                elif class_index == 2:    # Torso (put as bpart1)
                    detections.append({'frame':image_index+1, 'bpart':1,
                                       'name': 'Torso',
                                       'score':dets[i,-1], 'bbox':bbox})
                else: # OK
                    detections.append({'frame':image_index+1, 'bpart':class_index,
                                       'name': body_part_class,
                                       'score':dets[i,-1], 'bbox':bbox})
    return detections




def get_images():
    '''
    Get images by asking user for input
    '''
    cur_path = BASE_PATH

    # Get camera number
    print "Which camera would you like to get data from (Accepted: 1 through 3): ",
    cam_number = str(input())
    cur_path += cam_number

    # Get day
    per_day_dirs = os.listdir(cur_path)
    print("\t Days recorded on camera {}".format(cam_number))
    for i, day in enumerate(per_day_dirs):
        print day,
        if (i+1) % 10 == 0:
            print ""
    day_input = ""
    while day_input not in per_day_dirs:
        print "\n\nWhich of the dates above do you want to get data from: ",
        day_input = str(input())
    cur_path += "/" + day_input

    # Get hour
    per_hour_dirs = sorted(os.listdir(cur_path))
    print("\t Hours -- (Minutes) recorded on camera {} on day {}".format(cam_number, day_input))
    for i, hour in enumerate(per_hour_dirs):
        minute_range = list_to_ranges(os.listdir(cur_path + "/" + str(hour)), pretty=True)
        print hour, "--", minute_range
    hour_input = ""
    while hour_input not in per_hour_dirs:
        print "\n\nWhich of the hours above do you want to get data from: ",
        hour_input = str(input())
    cur_path += "/" + hour_input

    # Get images
    per_minute_dirs = sorted(os.listdir(cur_path))
    images = []
    for i, minute in enumerate(per_minute_dirs):
        images += sorted(glob.glob(cur_path + "/" + minute + "/*image.jpg"))

    # Get id for images
    path_base = os.path.basename(images[0])
    year  = path_base[:4]
    month = path_base[4:6]
    day   = path_base[6:8]
    hour  = path_base[8:10]
    images_id = "{}_{}_{}_{}".format(year, month, day, hour)

    return images, images_id




'''
Finds ranges in a list of numbers. (helper function)
'''
def list_to_ranges(num_list, pretty=False):
    ranges = []
    num_list = sorted([int(x) for x in num_list])
    num_list.append(max(num_list) + 10) # Takes care of final range
    cur_range_start = num_list[0]
    x_prev          = num_list[0]

    for x in num_list[1:]:
        if x != x_prev+1:
            ranges.append((x_prev, ) if x_prev == cur_range_start else (cur_range_start, x_prev))
            cur_range_start = x
        x_prev = x

    if pretty == True:
        pretty_ranges = []
        for r in ranges:
            pretty_ranges.append("{}-{}".format(r[0],r[1]) if len(r) == 2 else "{}".format(r[0]))
        return ", ".join(pretty_ranges)
    else:
        return ranges






def visualize_detections(rgb_images, detections):
    '''
    Draw bboxes on some of the images and save them to a video
    '''
    for image_index, image in enumerate(rgb_images):
        if image_index % 100 != 0:
            continue
        im = decrypt_image(image)
        #Find the bounding box for the image
        for det in detections:
            if det['frame'] == image_index+1:
                b = det['bbox']
                cv2.rectangle(im, (int(b[0]),int(b[1])),
                              (int(b[2]),int(b[3])), (0, 0, 255), 2)
                cv2.putText(im, det['name'], (int(b[0]),int(b[1])),
                            cv2.FONT_HERSHEY_PLAIN, 2, 255)
                cv2.imwrite('{}{:06d}.jpg'.format(detector_example_dir, image_index), im)




class suppress_stdout_stderr(object):
    '''
    Context manager to suppress stdout and stderr.
    This is to silence all of the output from loading the caffemodel.
    '''
    def __init__(self):
        # Open a pair of null files
        self.null_fds =  [os.open(os.devnull,os.O_RDWR) for x in range(2)]
        # Save the actual stdout (1) and stderr (2) file descriptors.
        self.save_fds = (os.dup(1), os.dup(2))

    def __enter__(self):
        # Assign the null pointers to stdout and stderr.
        os.dup2(self.null_fds[0],1)
        os.dup2(self.null_fds[1],2)

    def __exit__(self, *_):
        # Re-assign the real stdout/stderr back to (1) and (2)
        os.dup2(self.save_fds[0],1)
        os.dup2(self.save_fds[1],2)
        # Close the null files
        os.close(self.null_fds[0])
        os.close(self.null_fds[1])




def check_images(rgb_images, depth_images):
    '''
    Make sure depth and rgb have the same number of images
    '''
    if not rgb_images or not depth_images:
        raise ValueError(
            "ERROR: No rgb or depth images in this path " + \
            "Perhaps you input an incorrect folder path or extension?")
    if len(rgb_images) != len(depth_images):
        raise ValueError(
            "ERROR: Number of rgb images differs from depth images. " + \
            "There are " + str(len(rgb_images)) + "rgb images" + \
            "There are " + str(len(depth_images)) + "depth images")




def decrypt_image(image_file):
    '''
    Decrypt image
    '''
    fileAsData = np.fromfile(image_file, np.int8)
    bytesRemaining = fileAsData.size
    while bytesRemaining > 0:
        blockStart = fileAsData.size - bytesRemaining
        blockSize = np.minimum(bytesRemaining, KEY.size)
        fileAsData[blockStart:blockStart+blockSize] -= KEY[:blockSize]
        bytesRemaining -= blockSize
    fileInMemory = StringIO(fileAsData.tostring())
    dataImage = Image.open(fileInMemory)
    dataArray = np.fromstring(str(dataImage.tobytes()), dtype=np.uint8)
    dataArray = dataArray.reshape([dataImage.size[1], dataImage.size[0], 3])
    fileInMemory.close()
    pil_img = Image.fromarray(dataArray)
    cv2_img = np.array(pil_img)
    return cv2_img[:,:,::-1].copy()




if __name__ == '__main__':
    main()
