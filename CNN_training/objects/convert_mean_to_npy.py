#!/usr/bin/env python

import os
import sys

import numpy as np

from caffe.proto import caffe_pb2
from caffe import io



def main(args=None, parser=None):

    blob = caffe_pb2.BlobProto()
    data = open("imagenet_mean.binaryproto", "rb").read()
    blob.ParseFromString(data)
    nparray = io.blobproto_to_array(blob)
    the_mean = nparray[0]
    np.save("imagenet_mean.npy", the_mean)
    
    # Exit the application
    return 0


if __name__ == '__main__':
    sys.exit(main())


