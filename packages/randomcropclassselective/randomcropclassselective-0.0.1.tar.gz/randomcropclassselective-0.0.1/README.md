# Random Crop Class Selective

This is a simple custom Albumentations transform which acts as a random crop
while ensuring that specific classes will be preserved in the crop
post-transformation. 

This may be useful if it is desired to create augmentations of rare classes, to
ensure that these rare classes will actually be present in the augmentation.