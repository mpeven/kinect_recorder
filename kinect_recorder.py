import freenect
import cv2, av
import os, sys
import glob, shutil
import numpy as np
import pandas as pd
pd.set_option('display.width', 200)
pd.set_option('display.max_rows', 30)
pd.set_option('display.max_columns', 30)
pd.set_option('display.precision', 4)
import logging
from logging.handlers import TimedRotatingFileHandler
import time, datetime as dt
import json
import tarfile
from concurrent.futures import ProcessPoolExecutor
from nacl.public import PrivateKey, PublicKey, Box
from multiprocessing import Process, Value


def test():
    keep_running = Value('i', True, lock=False)
    recorder = KinectRecorder(keep_running)
    recorder.start()
    proc = KinectProcessor(keep_running)
    proc.start()




# File names
rgb_vid_file = 'rgb_vid.avi'
depth_vid_file = 'depth_vid.avi'
metadata_file = 'metadata.json'
client_public_key_file = 'client_key.pub'
rambo_public_key_file = 'rambo_key.pub'

# Directories and paths
base = os.path.dirname(os.path.realpath(__file__))
tar_dir = os.path.join(base, 'data')
tmp_dir = os.path.join(base, 'tmp')
key_dir = os.path.join(base, 'keys')
log_dir = os.path.join(base, 'logs')
rgb_img_dir = os.path.join(tmp_dir, 'rgb_imgs')
depth_img_dir = os.path.join(tmp_dir, 'depth_imgs')
rgb_vid_file_path = os.path.join(tmp_dir, rgb_vid_file)
depth_vid_file_path = os.path.join(tmp_dir, depth_vid_file)
metadata_file_path = os.path.join(tmp_dir, metadata_file)
client_public_key_file_path = os.path.join(tmp_dir, client_public_key_file)
rambo_public_key_file_path = os.path.join(key_dir, rambo_public_key_file)

# Time related stuff
TIME_FMT = '%Y_%m_%d_%H_%M_%S_%f'
minutes_to_wait = 2


class KinectRecorder(Process):
    def __init__(self, keep_running):
        Process.__init__(self)
        self.keep_running = keep_running
	# Set logging configuration
        filehandler = TimedRotatingFileHandler(log_dir + "/" + 'log', when="m", interval=1)
        streamhandler = logging.StreamHandler(stream=sys.stdout)
        logging.basicConfig(
            level=logging.DEBUG,
            handlers=[streamhandler, filehandler],
        )




    def run(self):
        '''
        Record until a keyboard interrupt
        '''
        try:
            self._run()
        except KeyboardInterrupt:
            print("Keyboard interrupt - exiting recorder")
            self.keep_running.value = False
            self.stop()




    def _run(self):
        '''
        Record images until self.keep_running is set to false
        '''
        # Turn light blinking green
        self.set_led(4)

        # Make image directories if they don't exist
        for directory in [tar_dir, tmp_dir, rgb_img_dir, depth_img_dir]:
            if not os.path.isdir(directory):
                os.mkdir(directory)

        # Save images
        logging.info("Recording images")
        while self.keep_running.value:
            rgb_data,_ = freenect.sync_get_video()
            depth_data,_ = freenect.sync_get_depth()

            timestamp = dt.datetime.now().strftime(TIME_FMT)
            rgb_file = os.path.join(rgb_img_dir, timestamp + '.jpg')
            depth_file = os.path.join(depth_img_dir, timestamp + '.png')

            cv2.imwrite(rgb_file, rgb_data[:, :, ::-1])
            cv2.imwrite(depth_file, depth_data.astype(np.uint16))

        # Clean up
        self.stop()




    def set_led(self, color):
        '''
        Change color of led on the front of the kinect
        '''
        kinect_ctx = freenect.init()
        kinect = freenect.open_device(kinect_ctx, 0)
        freenect.set_led(kinect, color)
        freenect.close_device(kinect)




    def stop(self):
        '''
        Stop recording and clean up temporary images
        '''
        logging.info("Stopping recording")
        freenect.sync_stop()
        self.set_led(0)
        logging.info("Cleaning up tmp files")
        shutil.rmtree(tmp_dir)





class KinectProcessor(Process):
    def __init__(self, keep_running):
        Process.__init__(self)
        self.keep_running = keep_running

    def run(self):
        try:
            self._run()
        except KeyboardInterrupt:
            print("Keyboard interrupt - exiting processor")
            pass

    def _run(self):
        while self.keep_running:
            time.sleep(10)

            # Get images and metadata
            image_files = self.get_images()
            if image_files is None:
                continue

            # Make videos and metadata
            self.make_video(rgb_vid_file_path, image_files['rgb_imgs'])
            self.make_video(depth_vid_file_path, image_files['depth_imgs'], depth=True)
            self.make_metadata(image_files['time_list'])

            # Encrypt the videos
            tmp_private_key = PrivateKey.generate()
            self.encrypt_file(tmp_private_key, rgb_vid_file_path)
            self.encrypt_file(tmp_private_key, depth_vid_file_path)

            # Save public key so rambo can use it to decrypt
            with open(client_public_key_file_path, 'wb') as f:
                f.write(tmp_private_key.public_key.encode())

            # Tar the videos, metadata, and public key
            file_prefix = image_files['minute'].strftime("%Y%m%d%H%M%S")
            tar_file_path = os.path.join(tar_dir, file_prefix + '.tar')
            self.make_tar(tar_file_path, file_prefix + "_")

            # Delete old files
            for i in image_files['rgb_imgs'] + image_files['depth_imgs']:
                os.remove(i)
            os.remove(rgb_vid_file_path)
            os.remove(depth_vid_file_path)
            os.remove(metadata_file_path)
            os.remove(client_public_key_file_path)



    def encrypt_file(self, client_private_key, file_to_encrypt):
        with open(rambo_public_key_file_path, 'rb') as f:
            rambo_public_key = PublicKey(f.read())
        client_box = Box(client_private_key, rambo_public_key)
        with open(file_to_encrypt, 'rb') as f:
            file_bytes = f.read()
        with open(file_to_encrypt, 'wb') as f:
            f.write(client_box.encrypt(file_bytes))



    def make_tar(self, tar_file_path, prefix):
        logging.info("Making tar file: {}".format(tar_file_path))
        with tarfile.open(tar_file_path, 'w') as f:
            f.add(rgb_vid_file_path, prefix + rgb_vid_file)
            f.add(depth_vid_file_path, prefix + depth_vid_file)
            f.add(metadata_file_path, prefix + metadata_file)
            f.add(client_public_key_file_path, prefix + client_public_key_file)



    def make_metadata(self, time_list):
        logging.info("Making metadata file: {}".format(metadata_file_path))
        string_time_list = ["{}".format(t) for t in time_list]
        json.dump(string_time_list, open(metadata_file_path, 'w+'))



    def make_video(self, vid_name, image_list, depth=False):
        logging.info("Making video file: {}".format(vid_name))
        pix_fmt = 'gray16' if depth else 'yuv420p'
        frame_fmt = 'gray16' if depth else 'bgr24'
        codec = 'ffv1' if depth else 'libx264'

        vid = av.open(vid_name, mode='w')
        vid_stream = vid.add_stream(codec, 24)
        vid_stream.pix_fmt = pix_fmt
        img0 = cv2.imread(image_list[0])
        height, width, _ = img0.shape
        vid_stream.height = height
        vid_stream.width = width

        for i in image_list:
            image = cv2.imread(i, -1)
            frame = av.VideoFrame(width, height, frame_fmt)
            frame.planes[0].update(image)
            packet = vid_stream.encode(frame)
            if packet:
                vid.mux(packet)

        vid.close()




    def get_images(self):
        # Check if there is enough data recorded
        if len(sorted(glob.glob(os.path.join(rgb_img_dir, '*')))) < 1:
            logging.info("Not enough data recorded - waiting")
            return None

        # Create dataframe with all images and timestamps
        df = pd.DataFrame()
        df['rgb_imgs'] = sorted(glob.glob(os.path.join(rgb_img_dir, '*')))
        df['depth_imgs'] = df['rgb_imgs'].apply(lambda x: x.replace('rgb', 'depth').replace('jpg', 'png'))
        df['time'] = pd.to_datetime(df['rgb_imgs'], format=os.path.join(rgb_img_dir, TIME_FMT + '.jpg'))
        df['time_to_minute'] = df['time'].apply(lambda x: x.replace(second=0, microsecond=0))

        time0 = df['time_to_minute'].iloc[0]

        # Make sure a few minutes have elapsed
        if time0 + dt.timedelta(minutes = minutes_to_wait) > dt.datetime.now():
            logging.info("Waiting for {} minutes to elapse before tarring data".format(minutes_to_wait))
            return None

        # Get list of all images with same minute as the first
        sub_df = df[df['time_to_minute'] == time0]

        return {
            'minute':     time0,
            'rgb_imgs':   list(sub_df['rgb_imgs']),
            'depth_imgs': list(sub_df['depth_imgs']),
            'time_list':  list(df['time']),
        }

if __name__ == '__main__':
    test()
