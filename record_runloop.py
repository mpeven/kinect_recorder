import freenect
import cv2
import numpy as np
import logging
logging.basicConfig(level=logging.DEBUG)
import datetime as dt

class KinectRecorder:
    def __init__(self, loop):
        self.keep_running = True
        self.loop = loop
        self.depth_queue = asyncio.Queue(loop=loop)
        self.image_queue = asyncio.Queue(loop=loop)
        self.record_period = dt.timedelta(minutes = 1)


    def start(self):
        ''' Schedule the asyncronous functions to start running '''
        try:
            # Start kinect
            freenect.runloop(depth=self.get_depth, video=self.get_rgb, body=self.body)
            # Start data processing
            self.loop.run_until_complete(self.record, loop=self.loop)
        except KeyboardInterrupt:
            logging.info("Keyboard interrupt - Exiting")
            pass
        finally:
            self.loop.close()


    def stop(self):
        ''' Stop recording '''
        logging.info("Received call to 'stop' - Exiting")
        self.keep_running = False


    async def record(self):
        ''' Record forever '''
        while self.keep_running:
            # Get times to record between
            time_start = dt.datetime.now()
            time_end = time_start + self.record_period
            # Get video
            depth_video, image_video = await self.make_video(time_start, time_end)


    async def make_video(self, start_time, end_time, video_image, video_depth):
        ''' Make a video file from the images between two timestamps '''

        # Create video writer objects
        video_image = cv2.VideoWriter(rgb_file, self.fourcc, self.fps, self.dims)
        video_depth = cv2.VideoWriter(depth_file, self.fourcc, self.fps, self.dims, False)

        # Loop until video is done
        while self.keep_running:
            # Get the raw data
            data_depth, timestamp_depth = await depth_queue.get()
            data_image, timestamp_image = await image_queue.get()

            # Check for drift
            if math.abs(timestamp_depth - timestamp_image) > 1:
                logging.error("Drift detected between depth ({}) and image ({})"\
                              .format(timestamp_depth, timestamp_image))

            # Process the images
            image = cv2.cvtColor(data_image, cv2.COLOR_RGB2BGR)

            # Add to video


            # Return files






    async def get_depth(self, dev, data, timestamp):
        await self.depth_queue.put((data, timestamp))

    async def get_rgb(dev, data, timestamp):
        await self.image_queue.put((data, timestamp))

    def body(self, *args):
        if not keep_running:
            raise freenect.Kill




