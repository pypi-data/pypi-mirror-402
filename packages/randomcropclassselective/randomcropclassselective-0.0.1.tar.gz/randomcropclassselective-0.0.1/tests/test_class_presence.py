import pytest
import numpy as np
import albumentations as A
from randomcropclassselective.random_crop_class_selective import RandomCropClassSelective

TRANSFORM = transform = A.Compose(
    [
        RandomCropClassSelective(crop_height=256,
                                 crop_width=256,
                                 required_classes=[999],
                                 max_attempts=200,
                                 p=1.0)
    ],
    bbox_params=A.BboxParams(format='albumentations',
                             label_fields=['class_labels'])
)

BLANK_IMAGE = np.zeros((512, 512, 3), dtype=np.uint8)

@pytest.fixture()
def setup():
    print('setup')
    yield "hello world"
    print('teardown')

class TestClassPresence:
    def test_required_class_does_not_exist(self):
        """
        Test required class does not appear if such class does not exist in the
        first place.
        """

        bboxes = [[0, 0, 0.1, 0.1]]
        class_labels = [0]

        augmented = TRANSFORM(image=BLANK_IMAGE,
                              bboxes=bboxes,
                              class_labels=class_labels)

        transformed_class_labels = augmented['class_labels']

        assert 999 not in transformed_class_labels

    def test_required_class_present_after_transformation(self):
        """
        Test required class is present in the post-cropping transformation.
        """

        bboxes = [[0, 0, 0.1, 0.1]]
        class_labels = [999]

        for i in range(1_000):
            augmented = TRANSFORM(image=BLANK_IMAGE,
                                bboxes=bboxes,
                                class_labels=class_labels)

            transformed_class_labels = augmented['class_labels']

            assert 999 in transformed_class_labels

        