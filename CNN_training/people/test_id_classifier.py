import numpy as np
import sys, os
import cv, cv2

import caffe

from liblinearutil import *


def main(args=None, parser=None):

	# Setup the CNN
	mean = np.load('imagenet_mean.npy')
	model_file = '/home/austin/dev/ThirdParty/caffe/models/bvlc_reference_caffenet/deploy.prototxt'
	pretrained_file = '/home/austin/dev/ThirdParty/caffe/models/bvlc_reference_caffenet/bvlc_reference_caffenet.caffemodel'
	net = caffe.Classifier(model_file, pretrained_file, image_dims=(256, 256), gpu=True, mean=mean, raw_scale=255, channel_swap=(2,1,0))

	# Setup the SVM
	idsvm = load_model('color_id_train.fc7.svm')
	

	# Load testing images--color only for ID classification
	color_entries = []
	ifs = open('color_id_svmtest.txt', 'r')
	while True:
		L = ifs.readline()
		if len(L) == 0:
			break
		S = L.split()

		img_file = S[0]
		label = int(S[1])

		color_entries.append((img_file,label))
	ifs.close()

	# Go through each, compute the fc7 feature, and classify with the SVM
	numCorrect = 0
	labelf = open('labelfile.txt', 'w')
	for i in range(0,len(color_entries)):
		img_file = color_entries[i][0]
		expected_label = color_entries[i][1]

		print (i+1), '/', len(color_entries)

		color_img = caffe.io.load_image(img_file)
		prediction = net.predict([color_img])

		# Get the feature
		feat = net.blobs['fc7'].data[0]
		featfc7 = feat.flatten()

		# Pump it through the SVM
		expectedLabelVec = np.zeros(1, dtype='int64')
		expectedLabelVec[0] = expected_label
		featfc7Vec = np.zeros((1, len(featfc7)))
		featfc7Vec[0] = featfc7
		p_label, p_acc, p_val = predict(expectedLabelVec.tolist(), featfc7Vec.tolist(), idsvm, '-q')

		# How did we do?
		#
		# 0 = patient
		# 1 = caregiver
		# 2 = family
		#
		tmp = []
		for i in range(0,len(p_label)):
			tmp.append(str(p_label[i])+',')

		for i in range(0,len(p_acc)):
			tmp.append(str(p_acc[i])+',')

		for i in range(0,len(p_val[0])-1):
			tmp.append(str(p_val[0][i])+',')
		i = len(p_val[0])-1
		tmp.append(str(p_val[0][i])+'\n')
		labelf.writelines(tmp)

		print 'Expected label:', expected_label, '; Predicted label:', p_label[0]
		if p_label[0] == expected_label:
			numCorrect = numCorrect + 1

	# How did we do in the end?
	print '\n\nTOTAL PERCENT CORRECT:', 100.0*float(numCorrect)/float(len(color_entries)), '%\n'
	labelf.close()

	# Exit application
	return 0


if __name__ == '__main__':
    sys.exit(main())		
