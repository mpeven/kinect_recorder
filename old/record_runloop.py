import freenect
import cv2
import os, glob
import logging
logging.basicConfig(level=logging.DEBUG)
import time, datetime as dt
import asyncio
from concurrent.futures import ProcessPoolExecutor


def test():
    loop = asyncio.get_event_loop()
    recorder = KinectRecorder(loop)
    recorder.start()


TIME_FMT = '%Y_%m_%d_%H_%M_%S_%f'


async def get_recorded_images():
    ''' Find all image files for the first minute '''

    # Get all images
    rgb_imgs = sorted(glob.glob('rgb_imgs/*'))
    depth_imgs = sorted(glob.glob('depth_imgs/*'))

    # Get all timestamps
    def get_timestamp_from_file(file_name):
        time_str = os.path.splitext(os.path.basename(file_name))[0]
        return dt.datetime.strptime(time_str, TIME_FMT)
    rgb_times = [get_timestamp_from_file(t) for t in rgb_imgs]
    depth_times = [get_timestamp_from_file(t) for t in depth_imgs]

    # Wait until at least a minute of recording is up
    if dt.datetime.now() - rgb_times[0] > dt.timedelta(minutes = 1):
        logging.info("Not enough data recorded - waiting for a minute")
        await asyncio.sleep(60)

    # Get all images in the same minute as the first timestamp
    first_minute = dt.datetime.now() - rgb_times[0]
    print(first_minute)


async def run_process_functions():
    images = await get_recorded_images()


def start_processing():
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(run_process_functions())
    except KeyboardInterrupt:
        logging.info("Caught it")
        loop.close()
        pass


class KinectRecorder:
    def __init__(self, loop):
        self.keep_running = True
        self.loop = loop
        self.executor = ProcessPoolExecutor(2)
        self.record_period = dt.timedelta(minutes = 1)
        self.kinect_ctx = freenect.init()



    def start(self):
        logging.info("Starting kinect recorder")
        try:
            all_tasks = [self.record_images(), self.process_images()]
            self.loop.run_until_complete(asyncio.gather(*all_tasks))
        except KeyboardInterrupt:
            logging.info("Received keyboard interrupt - Exiting")
            self.keep_running = False
        finally:
            self.executor.shutdown(wait=True)
            self.loop.close()
            freenect.sync_stop()
            self.set_led(0)



    def stop(self, *args):
        logging.info("Received call to 'stop' - Exiting")
        self.keep_running = False



    def set_led(self, color):
        kinect = freenect.open_device(self.kinect_ctx, 0)
        freenect.set_led(kinect, color)
        freenect.close_device(kinect)



    async def record_images(self):
        logging.info("Recording images")

        # Turn light blinking green
        self.set_led(4)

        # Make image directories if they don't exist
        for img_dir in ['rgb_imgs', 'depth_imgs']:
            if not os.path.isdir(img_dir):
                os.mkdir(img_dir)

        # Save images
        while self.keep_running:
            rgb_data,_ = freenect.sync_get_video()
            depth_data,_ = freenect.sync_get_depth()

            timestamp = dt.datetime.now().strftime(TIME_FMT)
            rgb_file = "rgb_imgs/{}.jpg".format(timestamp)
            depth_file = "depth_imgs/{}.png".format(timestamp)

            cv2.imwrite(depth_file, depth_data)
            cv2.imwrite(rgb_file, cv2.cvtColor(rgb_data, cv2.COLOR_RGB2BGR))

            await asyncio.sleep(0)



    async def process_images(self):
        logging.info("Processing images in another process")

        while self.keep_running:
            try:
                self.loop.run_in_executor(self.executor, start_processing)
            except KeyboardInterrupt:
                logging.info("Caught it 2")
                return









if __name__ == '__main__':
    test()
