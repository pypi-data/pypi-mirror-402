import albumentations as A
import pytest
import cv2
import numpy as np
from randomcropclassselective.random_crop_class_selective \
    import RandomCropClassSelective

CROP_SIDE_LENGTH = 256

TRANSFORM = transform = A.Compose(
    [
        RandomCropClassSelective(crop_height=CROP_SIDE_LENGTH,
                                 crop_width=CROP_SIDE_LENGTH,
                                 required_classes=[999],
                                 max_attempts=200,
                                 p=1.0)
    ],
    bbox_params=A.BboxParams(format='albumentations',
                             label_fields=['class_labels'])
)

TEST_IMAGE_PATH = "./tests/test.jpg"

@pytest.fixture()
def get_test_image():
    image = cv2.imread(TEST_IMAGE_PATH)
    yield image


class TestCropping:
    def test_random_crop(self, get_test_image):
        """
        Tests the transform actually creates a random crop of the input image.
        """

        image = get_test_image

        previous_augmentations = []

        for _ in range(10):
            augmented = TRANSFORM(image=image,
                                bboxes=[],
                                class_labels=[])

            assert not any(np.array_equal(augmented['image'], previous) 
                           for previous in previous_augmentations)

            previous_augmentations.append(augmented['image'])

    def test_crop_dimensions(self, get_test_image):
        """
        Tests the augmented image is the correct dimensions (as specified).
        """

        image = get_test_image

        augmented = TRANSFORM(image=image,
                              bboxes=[],
                              class_labels=[])

        assert augmented['image'].shape \
            == (CROP_SIDE_LENGTH, CROP_SIDE_LENGTH, 3)



