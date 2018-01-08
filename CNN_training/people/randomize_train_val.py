import os
import sys
import numpy as np


def main(args=None, parser=None):

	# The index text file name
	##indexFile = 'color_id_labels.txt'
	indexFile = 'depth_id_labels.txt'

	# Let's collect and write out the training and validation files
	##ofstrain = open('color_id_train.txt', 'w')
	##ofsval = open('color_id_val.txt', 'w')	
	##ofstest = open('color_id_test.txt', 'w')
	ofstrain = open('depth_id_train.txt', 'w')
	ofsval = open('depth_id_val.txt', 'w')	
	ofstest = open('depth_id_test.txt', 'w')

	# Load in the entries
	entries = []
	ifs = open(indexFile, 'r')
	while True:
		L = ifs.readline()
		if len(L) == 0:
			break
		S = L.split()

		img_file = S[0]
		label = int(S[1])

		entries.append((img_file,label))
	ifs.close()

	Nentries = len(entries)
	print '\nRetrieved', Nentries, 'entries'

	# Let's randomly permute them
	randi = np.random.permutation(Nentries)

	# Let's split into train, validate, and test
	trainRatio = 0.75
	valRatio = 0.12
	Ntrain = int(trainRatio*Nentries)
	Nval = int(valRatio*Nentries)
	Ntest = Nentries - Ntrain - Nval
	print 'Training with:', Ntrain, '; Validating with:', Nval, '; Testing with:', Ntest, '\n'
	
	kk = 0
	for i in range(0,Ntrain):
		j = randi[kk]
		e = entries[j]
		ofstrain.write(('%s %d\n' % (e[0], e[1])))
		kk = kk+1

	for i in range(0,Nval):
		j = randi[kk]
		e = entries[j]
		ofsval.write(('%s %d\n' % (e[0], e[1])))
		kk = kk+1

	for i in range(0,Ntest):
		j = randi[kk]
		e = entries[j]
		ofstest.write(('%s %d\n' % (e[0], e[1])))
		kk = kk+1

	ofstrain.close()
	ofsval.close()
	ofstest.close()

	# Exit application
	return 0


if __name__ == '__main__':
    sys.exit(main())	