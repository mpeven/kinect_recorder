clear all; close all; clc;
warning off;

% Setup Caffe
addpath('/home/austin/dev/ThirdParty/caffe/matlab/caffe');
use_gpu = 1;
model_def_file = 'deploy_color.prototxt';
model_file = 'finetune_color/finetune_person_id_color_iter_5000.caffemodel';
matcaffe_init(use_gpu, model_def_file, model_file);

% Read in the text file of test images
text = fileread('color_id_test.txt');
X = regexp(text, '\n', 'split');
numCorrect = 0;
numTotal = 0;
for i=1:length(X)
    Y = regexp(X{i}, ' ', 'split');
    
    if isempty(Y{1}) || isempty(Y{2})
        continue;
    end
    
    img_filename = Y{1};
    exp_label = str2double(Y{2});
    fprintf('Image file: %s\nExpected label: %d\n', img_filename, exp_label);

    % Load the image
    im = imread(img_filename);

    % prepare oversampled input
    % input_data is Height x Width x Channel x Num
    input_data = {prepare_image(im)};

    % do forward pass to get scores
    % scores are now Width x Height x Channels x Num
    scores = caffe('forward', input_data);

    scores = scores{1};
    scores = squeeze(scores);
    scores = mean(scores,2);

    % Get the best label
    [~,maxlabel] = max(scores);

    % Need to compensate for 0-based labels
    maxlabel=maxlabel-1;
    fprintf('Predicted label: %d\n\n', maxlabel);
    
    if maxlabel == exp_label
        numCorrect = numCorrect + 1;
    end
    numTotal = numTotal + 1;
end

fprintf('Percent correct: %.2f%%\n\n', 100.0*(numCorrect/numTotal));

