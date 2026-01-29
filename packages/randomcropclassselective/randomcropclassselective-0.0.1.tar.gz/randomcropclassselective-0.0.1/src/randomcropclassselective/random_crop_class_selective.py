from albumentations.core.transforms_interface import DualTransform
import numpy as np

class RandomCropClassSelective(DualTransform):
    """
    A custom Albumentations transform which acts as a random crop but 
    *attempting* to ensure that *at least one* of the classes provided in
    parameter `required_classes` will be present in the post-transformation
    crop.

    Falls back to a random crop if no crops were generated which contained
    *any* of the required classes within the number of maximum attempts.

    **NOTE!** This transform does *not* necessarily guarantee that there *will*
    be at least one required class present in the augmented image. The transform
    works by repeatedly generating crops until one is found where the required
    class is present in the crop. As such, it is possible that all attempts will
    be exhausted before any crop is found including a required class. The 
    `max_attempts` parameter can be adjusted to increase the number of times the
    transform will attempt to generate a crop, at the expense of running time.
    """

    def __init__(self, 
                 crop_height: int,
                 crop_width: int,
                 required_classes: list[int],
                 max_attempts: int = 50,
                 p: float = 0.5,):
        """
        :param crop_height: Height the image will be cropped to.
        :type crop_height: int
        :param crop_width: Width the image will be cropped to.
        :type crop_width: int
        :param required_classes: List of classes which should be included in the
            image after cropping.
        :type required_classes: list[int]
        :param max_attempts: Maximum number of attempts to crop the image such
            that at least one required class is present in the crop, before
            falling back to a random crop.
        :type max_attempts: int
        :param p: Probability this transformation is applied.
        :type p: float
        """
        
        super().__init__(p=p)

        self.crop_height = crop_height
        self.crop_width = crop_width

        self.original_width = -1
        self.original_height = -1

        self.required_classes = required_classes
        self.max_attempts = max_attempts

    def _does_crop_contain_required_class(self, 
                                          x1, y1, 
                                          x2, y2, 
                                          bboxes, 
                                          class_labels):
        """
        Returns `True` if the crop bounded by:
        - top-left corner (x1, y1)
        - bottom-right corner (x2, y2)

        ... contains at least any one required class (as defined in the 
        initialization of the transform).
        
        :param x1: Minimum x-coordinate.
        :param y1: Minimum y-coordinate.
        :param x2: Maximum x-coordinate.
        :param y2: Maximum y-coordinate.
        :param bboxes: List of bounding boxes in Albumentations format. 
        :param class_labels: List of class labels where each element corresponds
            to its respective bounding box at the same index in the `bboxes`
            list.
        """

        # normalize w.r.t original dimensions
        x1 /= self.original_width
        y1 /= self.original_height

        x2 /= self.original_width
        y2 /= self.original_height

        for class_label, bbox in zip(class_labels, bboxes):
            # skip non-required classes
            if class_label not in self.required_classes: 
                continue

            _x1, _y1, _x2, _y2 = bbox[:4]

            # if bounding box and cropped image intersect
            if not (x2 <= _x1 or x1 >= _x2 or y2 <= _y1 or y1 >= _y2):
                return True
        
        return False

    def get_params_dependent_on_data(self, params, data):
        self.original_height, self.original_width = params['shape'][:2]

        # bboxes format: (all normalized) [x_min, y_min, x_max, y_max, class_id]
        bboxes = data['bboxes']
        class_labels = [item[4] for item in bboxes]

        for _ in range(self.max_attempts):
            # top-left corner
            x1 = self.py_random.randint(0, 
                                        self.original_width - self.crop_width)
            y1 = self.py_random.randint(0, 
                                        self.original_height - self.crop_height)

            # bottom-right corner
            x2 = x1 + self.crop_width
            y2 = y1 + self.crop_height

            if self._does_crop_contain_required_class(x1, y1, 
                                                      x2, y2, 
                                                      bboxes, class_labels):
                return { "x1": x1, "y1": y1 }

        # fall back to random crop if max attempts exceeded
        return { "x1": x1, "y1": y1 }

    def apply(self, img, x1, y1, **params):
        return img[y1:y1+self.crop_height, x1:x1+self.crop_width]

    def apply_to_bboxes(self, bboxes: np.ndarray, x1, y1, **params):
        if len(bboxes) == 0:
            return np.empty((0, 0))

        bboxes_transformed = bboxes.copy()

        # set to absolute pixel value w.r.t. original dimensions
        bboxes_transformed[:, [0, 2]] *= self.original_width
        bboxes_transformed[:, [1, 3]] *= self.original_height

        # apply same transform as crop to bounding boxes
        bboxes_transformed[:, [0, 2]] -= x1
        bboxes_transformed[:, [1, 3]] -= y1

        # re-normalize w.r.t cropped dimensions
        bboxes_transformed[:, [0, 2]] /= self.crop_width
        bboxes_transformed[:, [1, 3]] /= self.crop_height

        return bboxes_transformed