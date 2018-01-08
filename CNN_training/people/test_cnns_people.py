import numpy as np
import sys, os
import cv, cv2

import caffe




def main(args=None, parser=None):

	# Make sure we're using the GPU
	caffe.set_mode_gpu()

	# Setup the CNN
	mean_ilsvrc = np.load('/home/austin/dev/ThirdParty/caffe/python/caffe/imagenet/ilsvrc_2012_mean.npy').mean(1).mean(1)
	model_file_color = 'deploy_color.prototxt'
	pretrained_file_color = 'finetune_color/finetune_person_id_color_iter_5000.caffemodel'
	net_color = caffe.Classifier(model_file_color, pretrained_file_color, image_dims=(256,256), mean=mean_ilsvrc, raw_scale=255, channel_swap=(2,1,0))
	#
	#
	model_file_depth = 'deploy_depth.prototxt'
	pretrained_file_depth = 'finetune_depth/finetune_person_id_depth_iter_5000.caffemodel'
	net_depth = caffe.Classifier(model_file_depth, pretrained_file_depth, image_dims=(256,256), mean=mean_ilsvrc, raw_scale=255, channel_swap=(2,1,0))

	# Load test images--color first
	color_entries = []
	ifs = open('color_id_test.txt', 'r')
	while True:
		L = ifs.readline()
		if len(L) == 0:
			break
		S = L.split()

		img_file = S[0]
		label = int(S[1])

		color_entries.append((img_file,label))
	ifs.close()

	# Then depth
	depth_entries = []
	ifs = open('depth_id_test.txt', 'r')
	while True:
		L = ifs.readline()
		if len(L) == 0:
			break
		S = L.split()
	
		img_file = S[0]
		label = int(S[1])
	
		depth_entries.append((img_file,label))
	ifs.close()

	# Class color images
	numCorrect=0
	numTotal=0
	for i in range(0,len(color_entries)):
		img_file = color_entries[i][0]
		expected_label = color_entries[i][1]

		color_img = caffe.io.load_image(img_file)
		prediction = net_color.predict([color_img])
		predicted_label = prediction[0].argmax()
		print '[COLOR] Expected class:', expected_label, '; Predicted label:', predicted_label
		numTotal = numTotal + 1
		if expected_label == predicted_label:
			numCorrect = numCorrect + 1
	percent_correct_color = float(numCorrect) / float(numTotal)

	# Classify depth images
	for i in range(0,len(depth_entries)):
		img_file = depth_entries[i][0]
		expected_label = depth_entries[i][1]
	
		depth_img = caffe.io.load_image(img_file)
		prediction = net_depth.predict([depth_img])
		predicted_label = prediction[0].argmax()
		print '[DEPTH] Expected class:', expected_label, '; Predicted label:', predicted_label
		numTotal = numTotal + 1
		if expected_label == predicted_label:
			numCorrect = numCorrect + 1
	percent_correct_depth = float(numCorrect) / float(numTotal)

	print '\nPercent correct [COLOR]:', 100.0*percent_correct_color, '%\n'
	print 'Percent correct [DEPTH]:', 100.0*percent_correct_depth, '%\n'

	# Exit application
	return 0


if __name__ == '__main__':
    sys.exit(main())		
