#!/usr/bin/env python3

import glob
import os, sys
import numpy as np
import io
from PIL import Image, ImageFilter, ImageDraw, ImageFont
from tqdm import tqdm
import cv2
import subprocess

BASE_PATH = "/edata/WICU_DATASET_2014/untar/WICU-room5_"
KEY_FILE = "/edata/WICU_DATASET_2014/demoTracking/key.bin"
KEY = np.fromfile(KEY_FILE, dtype=np.int8)


SKIP_NUMBER = 2


def main():
    image_paths_all = get_images()
    image_paths = [image_paths_all[i] for i in range(0, len(image_paths_all), SKIP_NUMBER)]

    print("Decrypting images")
    decrypted_images = [decrypt_image(i) for i in tqdm(image_paths)]
    print("Blurring images")
    blurred_images   = [blur_image(i) for i in tqdm(decrypted_images)]
    print("Adding text to images")
    im_path = zip(blurred_images, image_paths)
    final_images     = [draw_metadata(i[0], i[1]) for i in tqdm(im_path)]
    print("Turning images into video")
    imgs_to_vid(final_images, "test.mp4")


def main_auto():
    hour_paths = find_complete_hours(3)
    for hour_path in hour_paths:
        date = hour_path[-11:-3]
        hour = hour_path[-2:]
        print("Creating a video for {}:{}".format(date, hour))
        image_paths_all = get_images_in_path(hour_path)
        image_paths = [image_paths_all[i] for i in range(0, len(image_paths_all), SKIP_NUMBER)]
        print("Decrypting images")
        decrypted_images = [decrypt_image(i) for i in tqdm(image_paths)]
        print("Blurring images")
        blurred_images   = [blur_image(i) for i in tqdm(decrypted_images)]
        print("Adding text to images")
        im_path = zip(blurred_images, image_paths)
        final_images     = [draw_metadata(i[0], i[1]) for i in tqdm(im_path)]
        print("Turning images into video")
        imgs_to_vid(final_images, "/edata/VIDS_FOR_ANDY/{}_{}.mp4".format(date,hour))




'''
Get images
'''
def get_images():
    cur_path = BASE_PATH

    # Get camera number
    print("Which camera would you like to get data from (Accepted: 1 through 3): ", end="")
    cam_number = str(input())
    cur_path += cam_number


    # Get day
    per_day_dirs = os.listdir(cur_path)
    print("\t Days recorded on camera {}".format(cam_number))
    for i, day in enumerate(per_day_dirs):
        print(day, end="  ")
        if (i+1) % 10 == 0:
            print()
    day_input = ""
    while day_input not in per_day_dirs:
        print("\n\nWhich of the dates above do you want to get data from: ", end="")
        day_input = input()
    cur_path += "/" + day_input


    # Get hour
    per_hour_dirs = sorted(os.listdir(cur_path))
    print("\t Hours recorded on camera {} on day {}".format(cam_number, day_input))
    for i, hour in enumerate(per_hour_dirs):
        minute_range = list_to_ranges(os.listdir(cur_path + "/" + str(hour)), pretty=True)
        print(hour, minute_range)
    hour_input = ""
    while hour_input not in per_hour_dirs:
        print("\n\nWhich of the hours above do you want to get data from: ", end="")
        hour_input = input()
    cur_path += "/" + hour_input


    # Get images
    per_minute_dirs = sorted(os.listdir(cur_path))
    images = []
    for i, minute in enumerate(per_minute_dirs):
        images += sorted(glob.glob(cur_path + "/" + minute + "/*image.jpg"))

    return images



'''
Find all hours that have data in every minute
'''
def find_complete_hours(cam):
    all_hours = []
    cam_path = BASE_PATH + str(cam)
    for day in sorted(os.listdir(cam_path)):
        day_path = cam_path + "/" + day
        for hour in sorted(os.listdir(day_path)):
            hour_path = day_path + "/" + hour
            r = list_to_ranges(os.listdir(hour_path), pretty=True)
            if r == "0-59":
                all_hours.append(hour_path)
    return all_hours

'''
Get all images in an hour block given the path
'''
def get_images_in_path(hour_path):
    per_minute_dirs = sorted(os.listdir(hour_path))
    images = []
    for minute in per_minute_dirs:
        images += sorted(glob.glob(hour_path + "/" + minute + "/*image.jpg"))
    return images





'''
Decrypt image
'''
def decrypt_image(image_path):
    fileAsData = np.fromfile(image_path, np.int8)
    bytesRemaining = fileAsData.size
    while bytesRemaining > 0:
        blockStart = fileAsData.size - bytesRemaining
        blockSize = np.minimum(bytesRemaining, KEY.size)
        fileAsData[blockStart:blockStart+blockSize] -= KEY[:blockSize]
        bytesRemaining -= blockSize
    fileInMemory = io.BytesIO(fileAsData.tostring())
    dataImage = Image.open(fileInMemory)
    return dataImage




'''
Blur image
'''
def blur_image(image):
    return image.filter(ImageFilter.BoxBlur(8))




'''
Draw metadata on an image
'''
def draw_metadata(image, image_path):
    path_base = os.path.basename(image_path)
    year  = path_base[:4]
    month = path_base[4:6]
    day   = path_base[6:8]
    hour  = path_base[8:10]
    min   = path_base[10:12]
    sec   = path_base[12:14]
    milli = path_base[15:18]
    time_text = "{}/{}/{} {}:{}:{}.{}".format(year, month, day, hour, min, sec, milli)
    d = ImageDraw.Draw(image)
    font = ImageFont.truetype("/home/mpeven/Downloads/Roboto_Mono/RobotoMono-Regular.ttf", 24)
    d.text((10,30), time_text, font=font, fill=(255,0,0,255))
    return image




'''
Turn a bunch of images into a video
'''
def imgs_to_vid(images, vid_name):
    for i, image in enumerate(images):
        image.save('test/tmp_img{:08d}.jpg'.format(i))
    cmd = "ffmpeg -r 120 -i test/tmp_img%08d.jpg -vcodec libx264 -crf 25 -pix_fmt yuv420p {}".format(vid_name)
    subprocess.run(cmd, shell=True)
    subprocess.run("rm -f test/tmp_img*", shell=True)
    return





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




if __name__ == '__main__':
    main_auto()
