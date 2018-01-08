import numpy as np
import sys, os
import cv, cv2

import caffe




def main(args=None, parser=None):

	# Setup the CNN
	mean = np.load('imagenet_mean.npy')
	model_file = '/home/austin/dev/ThirdParty/caffe/models/bvlc_reference_caffenet/deploy.prototxt'
	pretrained_file = '/home/austin/dev/ThirdParty/caffe/models/bvlc_reference_caffenet/bvlc_reference_caffenet.caffemodel'
	net = caffe.Classifier(model_file, pretrained_file, image_dims=(256, 256), gpu=True, mean=mean, raw_scale=255, channel_swap=(2,1,0))
	

	# Load training images--color only for ID classification
	color_entries = []
	ifs = open('color_id_train.txt', 'r')
	while True:
		L = ifs.readline()
		if len(L) == 0:
			break
		S = L.split()

		img_file = S[0]
		label = int(S[1])

		color_entries.append((img_file,label))
	ifs.close()

	# Go through each, compute the fc7 feature, and save out to a text file
	#
	# each row is in libSVM format
	#
	ofs = open('color_id_train.fc7', 'w')
	for i in range(0,len(color_entries)):
		img_file = color_entries[i][0]
		expected_label = color_entries[i][1]

		print (i+1), '/', len(color_entries)

		color_img = caffe.io.load_image(img_file)
		prediction = net.predict([color_img])

		# Get the feature
		feat = net.blobs['fc7'].data[0]
		featfc7 = feat.flatten()

		# Save it
		ofs.write(('%d ' % (expected_label)))
		for j in range(0,len(featfc7)):
			ofs.write(('%d:%.7f ' % (j+1,featfc7[j])))
		ofs.write('\n')
	ofs.close()

	# Exit application
	return 0


if __name__ == '__main__':
    sys.exit(main())		
