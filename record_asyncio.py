import os
import freenect
import cv2
import numpy as np
import datetime as dt
import json
import logging
logging.basicConfig(level=logging.DEBUG)
import tarfile
import shutil
import asyncio, threading

def test():
    recorder = KinectRecorder("/home/mike/Documents/Sensor/kinect/test")
    recorder.start()
    import time
    time.sleep(10)
    print("calling recorder.stop()")
    recorder.stop()



class KinectRecorder(threading.Thread):
    def __init__(self, file_path, encrypt=True):
        threading.Thread.__init__(self)

        # File names and paths
        self.file_path = file_path
        self.tmp_path = os.path.join(file_path, "tmp_kinect_data")

        # Encrypt the video
        self.encrypt = encrypt

        # Video info
        self.dims = (640, 480)
        self.fps = 30.0
        self.vid_ext = ".avi"
        self.fourcc = cv2.VideoWriter_fourcc(*'x264') # x264 codec - small size, not very lossy

        # Kinect stuff
        self.kinect_ctx = freenect.init()


    def run(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.file_queue = asyncio.Queue(loop=self.loop)
        try:
            self.set_led(4) # Turn kinect led to flashing green
            os.mkdir(self.tmp_path) # Make temporary directory to save files
            self.keep_running = True
            self.loop.run_until_complete(asyncio.gather(
                self.record(),
                self.encrypt_and_tar(),
            ))
        except KeyboardInterrupt:
            self.keep_running = False
        finally:
            logging.info("Shutting down")
            self.loop.close()
            freenect.sync_stop()
            self.set_led(0)
            shutil.rmtree(self.tmp_path)


    def stop(self):
        logging.info("Got the message to stop recording")
        self.keep_running = False


    def set_led(self, color):
        kinect = freenect.open_device(self.kinect_ctx, 0)
        freenect.set_led(kinect, color)
        freenect.close_device(kinect)


    async def record(self):
        while self.keep_running:
            start_time = dt.datetime.now()
            end_time = start_time + dt.timedelta(seconds = 3)
            timestamp = start_time.strftime("%Y%m%d%H%M%S")

            rgb_file = os.path.join(self.tmp_path,
                                    "rgb_{}.{}".format(timestamp, self.vid_ext))
            depth_file = os.path.join(self.tmp_path,
                                      "depth_{}.{}".format(timestamp, self.vid_ext))
            metadata_file = os.path.join(self.tmp_path,
                                         "metadata_{}.json".format(timestamp))
            # Create VideoWriter objects (opens file descriptors in tmp folder), and metadata list
            out_rgb = cv2.VideoWriter(rgb_file, self.fourcc, self.fps, self.dims)
            out_depth = cv2.VideoWriter(depth_file, self.fourcc, self.fps, self.dims, False)
            metadata = []

            # Record for one minute at a time
            logging.info("Start recording at {}".format(dt.datetime.now()))
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
            logging.info("Stop recording at {}".format(dt.datetime.now()))

            # Save files
            out_rgb.release()
            out_depth.release()
            json.dump(metadata, open(metadata_file, 'w+'))

            # Put files on the queue
            await self.file_queue.put(timestamp)
            await self.file_queue.put((rgb_file, depth_file, metadata_file))

            # Yield to other tasks
            await asyncio.sleep(0)

        # Turned off, tell the file processing task to stop
        await self.file_queue.put(None)
        return


    async def encrypt_and_tar(self):
        ''' Encrypt and tar the files that get put on the queue '''
        while True:
            timestamp = await self.file_queue.get()

            # Message to exit loop
            if timestamp is None:
                return

            # Get the files
            logging.info("Getting files for recording starting at {}".format(timestamp))
            filenames = await self.file_queue.get()

            # Encrypt
            if self.encrypt:
                pass # TODO: encrypt

            # Tar
            await asyncio.sleep(0)
            tar = os.path.join(self.file_path, timestamp + ".tar")
            logging.info("Tarring files in {}".format(tar))
            with tarfile.open(tar, 'w') as tf:
                for f in filenames:
                    tf.add(f, os.path.basename(f))

            # Delete old files
            await asyncio.sleep(0)
            for f in filenames:
                os.remove(f)
            await asyncio.sleep(0)
            logging.info("Done encrypting and tarring")



# Test
if __name__ == '__main__':
    test()
