import os
import freenect
import cv2
import numpy as np
import datetime as dt
import json
import logging
logging.basicConfig(level=logging.DEBUG)
import threading
import tarfile
import shutil


'''
KinectRecorder

This records depth and rgb video using a kinect in its own thread.

Parameters:
    file_path  -  the full path to the directory to save the videos


Example:
    recorder = KinectRecorder("/home/rob/kinect/data")
    recorder.start()
'''

def test():
    recorder = KinectRecorder("/home/mike/Documents/Sensor/kinect/test")
    try:
        recorder.start()
        import time
        time.sleep(1200)
    except Exception as e:
        logging.info("Caught exception")
    finally:
        logging.info("Shutting down kinect")
        recorder.stop()



class KinectRecorder(threading.Thread):
    def __init__(self, file_path, encrypt=True):
        threading.Thread.__init__(self)
        self.file_path = file_path
        self.tmp_path = os.path.join(file_path, "tmp_" + dt.datetime.now().strftime("%Y%m%d%H%M%S"))
        self.encrypt = ecrypt
        self.keep_running = False
        self.dims = (640, 480)
        self.fps = 30.0
        self.fourcc = cv2.VideoWriter_fourcc(*'x264') # x264 codec - small size, not very lossy
        self.kinect_ctx = freenect.init()



    def set_led(self, color):
        kinect = freenect.open_device(self.kinect_ctx, 0)
        freenect.set_led(kinect, color)
        freenect.close_device(kinect)



    def run(self):
        '''
        Starts recording rgb and depth and saves it to 'file_path'
        They are saved as minute long videos, tarred together with a metadata
            file which contains the exact time the images were captured so that
            each frame can be extracted from the video with all its info
        '''
        self.keep_running = True

        # Set device led to flashing green
        self.set_led(4)

        # File names and paths
        rgb_name = "rgb.avi"
        depth_name = "depth.avi"
        metadata_name = "metadata.json"
        rgb_file = os.path.join(self.tmp_path, rgb_name)
        depth_file = os.path.join(self.tmp_path, depth_name)
        metadata_file = os.path.join(self.tmp_path, metadata_name)

        while self.keep_running:
            # Create VideoWriter objects (opens file descriptors in tmp folder), and metadata list
            os.mkdir(self.tmp_path)
            out_rgb = cv2.VideoWriter(rgb_file, self.fourcc, self.fps, self.dims)
            out_depth = cv2.VideoWriter(depth_file, self.fourcc, self.fps, self.dims, False)
            metadata = []

            # Record for one minute at a time
            start_time = dt.datetime.now()
            end_time = start_time + dt.timedelta(minutes = 1)
            logging.info("Start recording at {}".format(start_time))
            while self.keep_running:
                if dt.datetime.now() > end_time:
                    break

                # Get color image
                rgb_array,_ = freenect.sync_get_video()
                rgb_array = cv2.cvtColor(rgb_array, cv2.COLOR_RGB2BGR)

                # Get depth image
                depth_array,_ = freenect.sync_get_depth()
                depth_array = depth_array.astype(np.uint8)

                # Save images and metadata
                out_rgb.write(rgb_array)
                out_depth.write(depth_array)
                metadata.append(dt.datetime.now().strftime("%Y%m%d%H%M%S_%f")[:-3])

            # Save files
            out_rgb.release()
            out_depth.release()
            json.dump(metadata, open(metadata_file, 'w+'))

            # Tar files together (uncompressed)
            file_prefix = start_time.strftime("%Y%m%d%H%M%S")
            tar = os.path.join(self.file_path, file_prefix + ".tar")
            logging.info("Tarring files in {}".format(tar))
            with tarfile.open(tar, 'w') as f:
                f.add(rgb_file, file_prefix + "_" + rgb_name)
                f.add(depth_file, file_prefix + "_" + depth_name)
                f.add(metadata_file, file_prefix + "_" + metadata_name)

            # Delete old files
            shutil.rmtree(self.tmp_path)

        # Exited the record forever loop - shutdown device
        freenect.sync_stop()
        self.set_led(0)



    def stop(self):
        self.keep_running = False
        self.join()




# Test
if __name__ == '__main__':
    test()
