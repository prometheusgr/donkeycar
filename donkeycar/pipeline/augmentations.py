import logging
from donkeycar.config import Config

logger = logging.getLogger(__name__)


# Try to import albumentations; if unavailable provide a lightweight
# fallback so tests and environments without the package can still import
# and run without performing augmentations.
try:
    import albumentations.core.transforms_interface
    import albumentations as A
    from albumentations import GaussianBlur
    from albumentations.augmentations import RandomBrightnessContrast

    class ImageAugmentation:
        def __init__(self, cfg, key, prob=0.5):
            aug_list = getattr(cfg, key, [])
            augmentations = [ImageAugmentation.create(a, cfg, prob)
                             for a in aug_list]
            self.augmentations = A.Compose(augmentations)

        @classmethod
        def create(cls, aug_type: str, config: Config, prob) -> \
                albumentations.core.transforms_interface.BasicTransform:
            """ Augmentation factory.
            """
            if aug_type == 'BRIGHTNESS':
                b_limit = getattr(config, 'AUG_BRIGHTNESS_RANGE', 0.2)
                logger.info(f'Creating augmentation {aug_type} {b_limit}')
                return RandomBrightnessContrast(brightness_limit=b_limit,
                                                contrast_limit=b_limit,
                                                p=prob)

            elif aug_type == 'BLUR':
                b_range = getattr(config, 'AUG_BLUR_RANGE', 3)
                logger.info(f'Creating augmentation {aug_type} {b_range}')
                return GaussianBlur(sigma_limit=b_range, blur_limit=(13, 13),
                                    p=prob)

        # Parts interface
        def run(self, img_arr):
            if len(self.augmentations) == 0:
                return img_arr
            aug_img_arr = self.augmentations(image=img_arr)["image"]
            return aug_img_arr

except Exception:  # pragma: no cover - fallback for test/CI environments
    logger.warning(
        'albumentations not available; ImageAugmentation will be a no-op')

    class ImageAugmentation:  # minimal fallback
        def __init__(self, cfg, key, prob=0.5):
            self.augmentations = []

        @classmethod
        def create(cls, aug_type: str, config: Config, prob):
            return None

        def run(self, img_arr):
            return img_arr
