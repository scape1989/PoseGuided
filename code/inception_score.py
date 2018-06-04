import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils import data
from models import *
import numpy as np
from utils import *
from skimage.measure import compare_ssim as ssim
from skimage.color import rgb2gray
from scipy.stats import entropy
import os
from data_loader import Dataset
from torchvision.utils import save_image
from torchvision.models.inception import inception_v3
from PIL import Image

def inception_score(images,batch_size=16,resize=False,splits = 10):
	'''
	This function computes the inception score of generated images

	images: Torch tensor of shape (batch_size,channels,height,width)

	'''

	num_images = images.size(0)

	dtype = torch.FloatTensor


	#use a pre-trained inception model for evaluation
	inception_net = inception_v3(pretrained=True,transform_input=False).type(dtype)

	#use in evaluation mode
	inception_net.eval()

	#function to resize images
	up = nn.Upsample(size=(299, 299), mode='bilinear').type(dtype)

	#helper function to evaluate inception scores
	def score(x):
		if resize:
			x = up(x)
		logits = inception_net(x)
		return F.softmax(logits,dim=-1).data.numpy()

	scores = np.zeros((num_images,1000))

	dataloader = torch.utils.data.DataLoader(images, batch_size=batch_size)

	for i, batch in enumerate(dataloader, 0):
		batch = batch.type(dtype)
		batch_size_i = batch.size(0)
		scores[i*batch_size:i*batch_size + batch_size_i] = score(batch)

	print "Scores calculated! \n Now calculating KL KL-Divergence"

	#KL-Divergence calculation
	means = np.mean(scores,axis=0)

	split_scores = []

	for k in range(splits):
		split_i = scores[k*(num_images//splits):(k+1)*(num_images//splits),:]
		ms = np.mean(split_i, axis=0)
		entr = []
		for i in range(split_i.shape[0]):
			example = split_i[i, :]
			entr.append(entropy(example, ms))
		split_scores.append(np.exp(np.mean(entr)))

	return np.mean(split_scores), np.std(split_scores)

if __name__ == '__main__':
	class IgnoreLabelDataset(torch.utils.data.Dataset):
		def __init__(self, orig):
			self.orig = orig

		def __getitem__(self, index):
			return self.orig[index][0]

		def __len__(self):
			return len(self.orig)

	images = []
	path = '../test_result/G/'
	for filename in os.listdir(path):
		img = Image.open(path+filename,'r')
		img = np.array(img) #HWC
		img = np.transpose(img,[2,0,1])
		images.append(img)

	images = np.array(images).astype(np.float32)
	print images.shape

	print "Calculating Inception Score on generated images..."
	print inception_score(torch.from_numpy(images), batch_size=16, resize=True, splits=10)
	
	## Inception score for target images

	target_path = '../test_result/x_target/'
	target_images = []
	for filename in os.listdir(target_path):
		img = Image.open(target_path+filename,'r')
		img = np.array(img) #HWC
		img = np.transpose(img,[2,0,1])
		target_images.append(img)

	target_images = np.array(target_images).astype(np.float32)
	print target_images.shape

	print "Calculating Inception Score on target images..."
	print inception_score(torch.from_numpy(target_images), batch_size=16, resize=True, splits=10)



