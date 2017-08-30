import numpy as np
import cv2
import logging
logging.basicConfig(level=logging.DEBUG)

def compare_images(image1, image2):
    data1 = cv2.imread(image1, -1)
    data2 = cv2.imread(image2, -1)

    if data1.shape != data2.shape:
        raise ValueError("Can't compare images - they have different dimensions")

    differences = data1 != data2
    num_diff = sum(sum(differences))
    percent_diff = num_diff / (data1.shape[0] * data1.shape[1]) * 100
    logging.info("Found {} differences between image 1 and 2 ({:.2f}%)".format(
        num_diff, percent_diff))
    if(num_diff == 0):
        return
    difference_total = 0.0
    for row in range(differences.shape[0]):
        for col in range(differences.shape[1]):
            if data1[row, col] != data2[row, col]:
                difference_total += abs(float(data1[row, col]) - float(data2[row, col]))
    avg_diff = difference_total / num_diff
    logging.info("Average difference: {:.2f}".format(avg_diff))
