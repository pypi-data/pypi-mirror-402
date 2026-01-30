import os
import numpy as np
import pandas as pd
from mosamatic2.core.tasks.task import Task
from mosamatic2.core.managers.logmanager import LogManager
from mosamatic2.core.data.multidicomimage import MultiDicomImage
from mosamatic2.core.data.numpyimage import NumpyImage
from mosamatic2.core.utils import (
    get_pixels_from_dicom_object,
    calculate_area,
    calculate_mean_radiation_attenuation,
    calculate_lama_percentage,
    get_pixels_from_tag_file,
    MUSCLE,
    SAT,
    VAT,
)

LOG = LogManager()


class ApplyThresholdToSegmentationsTask(Task):
    INPUTS = [
        'images',
        'segmentations'
    ]
    PARAMS = [
        'label',
        'threshold_low', 
        'threshold_high'
    ]

    def __init__(self, inputs, params, output, overwrite=True):
        super(ApplyThresholdToSegmentationsTask, self).__init__(inputs, params, output, overwrite)

    def collect_image_segmentation_pairs(self, images, segmentations, file_type='npy'):
        file_type = '.tag' if file_type == 'tag' else '.seg.npy'
        img_seg_pairs = []
        for image in images:
            f_img_path = image.path()
            f_img_name = os.path.split(f_img_path)[1]
            for f_seg_path in segmentations:
                f_seg_name = os.path.split(f_seg_path)[1]
                if file_type == '.seg.npy':
                    f_seg_name = f_seg_name.removesuffix(file_type)
                    if f_seg_name == f_img_name:
                        img_seg_pairs.append((image, f_seg_path))
                elif file_type == '.tag':
                    f_seg_name = f_seg_name.removesuffix(file_type).removesuffix('.dcm')
                    f_img_name = f_img_name.removesuffix('.dcm')
                    if f_seg_name == f_img_name:
                        img_seg_pairs.append((image, f_seg_path))
                else:
                    raise RuntimeError('Unknown file type')
        return img_seg_pairs

    def load_images(self):
        image_data = MultiDicomImage()
        image_data.set_path(self.input('images'))
        if image_data.load():
            return image_data
        raise RuntimeError('Could not load images')
    
    def load_pixels_and_spacing(self, image):
        p = image.object()
        pixels = get_pixels_from_dicom_object(p, normalize=True)
        return pixels, p.PixelSpacing

    def load_segmentations(self, file_type='npy'):
        file_type = '.tag' if file_type == 'tag' else '.seg.npy'
        segmentations = []
        for f in os.listdir(self.input('segmentations')):
            f_path = os.path.join(self.input('segmentations'), f)
            if f.endswith(file_type):
                segmentations.append(f_path)
        if len(segmentations) == 0:
            raise RuntimeError('Input directory has no segmentation files')
        return segmentations

    def load_segmentation(self, f, file_type='npy'):
        if file_type == 'npy':
            segmentation = NumpyImage()
            segmentation.set_path(f)
            if segmentation.load():
                return segmentation.object()
            LOG.error(f'Could not load segmentation file {f}')
        if file_type == 'tag':
            pixels = get_pixels_from_tag_file(f)
            try:
                pixels = pixels.reshape(512, 512)
                return pixels
            except Exception:
                LOG.warning(f'Could not reshape TAG pixels to (512, 512), skipping...')
                return None
        raise RuntimeError('Unknown file type')

    def run(self):
        images = self.load_images().images()
        segmentations = self.load_segmentations()
        image_segmentation_pairs = self.collect_image_segmentation_pairs(images, segmentations)
        threshold_low = self.param('threshold_low')
        threshold_high = self.param('threshold_high')
        label = self.param('label')
        nr_steps = len(image_segmentation_pairs)
        for step in range(nr_steps):
            image, pixel_spacing = self.load_pixels_and_spacing(image_segmentation_pairs[step][0])
            segmentation = self.load_segmentation(image_segmentation_pairs[step][1])
            area = calculate_area(segmentation, label, pixel_spacing)
            LOG.info(f'area: {area} mm')
            segmentation_new = segmentation.copy()
            segmentation_new[(segmentation_new == label) & (image < threshold_low)] = 0
            area_new = calculate_area(segmentation_new, label, pixel_spacing)
            LOG.info(f'area_new: {area_new} mm')
            segmentation_new_file_name = os.path.split(image_segmentation_pairs[step][0].path())[1]
            segmentation_new_file_path = os.path.join(self.output(), f'{segmentation_new_file_name}.seg.npy')
            np.save(segmentation_new_file_path, segmentation_new)
            self.set_progress(step, nr_steps)