import os
import numpy as np
import SimpleITK as sitk
from mosamatic2.core.tasks.task import Task
from mosamatic2.core.managers.logmanager import LogManager
from mosamatic2.core.utils import (
    is_dicom, 
    convert_numpy_array_to_png_image, 
    convert_dicom_to_png_image,
    AlbertaColorMap,
)

LOG = LogManager()


class SegmentationNumpy2NiftiTask(Task):
    INPUTS = ['images', 'segmentations']
    PARAMS = []

    def __init__(self, inputs, params, output, overwrite):
        super(SegmentationNumpy2NiftiTask, self).__init__(inputs, params, output, overwrite)

    def load_images(self):
        images = []
        for f in os.listdir(self.input('images')):
            f_path = os.path.join(self.input('images'), f)
            if is_dicom(f_path):
                images.append(f_path)
        return images

    def load_segmentations(self):
        segmentations = []
        for f in os.listdir(self.input('segmentations')):
            if f.endswith('.seg.npy'):
                f_path = os.path.join(self.input('segmentations'), f)
                segmentations.append(f_path)
        return segmentations
    
    def create_pairs_of_images_and_segmentations(self, images, segmentations):
        pairs = []
        for segmentation in segmentations:
            for image in images:
                image_name = os.path.split(image)[1]
                if image_name in os.path.split(segmentation)[1]:
                    pairs.append((image, segmentation))
        return pairs
    
    def load_segmentation_as_narray(self, segmentation):
        narray = np.load(segmentation)
        return narray
    
    def create_png_from_dicom(self, file_path):
        convert_dicom_to_png_image(file_path, self.output())

    def create_png_from_array(self, data, file_path):
        png_file_name = os.path.split(file_path)[1] + '.png'
        convert_numpy_array_to_png_image(
            data, 
            self.output(),
            AlbertaColorMap(), 
            png_file_name,
            fig_width=10, fig_height=10,
        )


    def run(self):
        images = self.load_images()
        segmentations = self.load_segmentations()        
        image_and_segmentation_pairs = self.create_pairs_of_images_and_segmentations(images, segmentations)
        nr_steps = len(image_and_segmentation_pairs)
        for step in range(nr_steps):
            pair = image_and_segmentation_pairs[step]
            # Load segmentation
            segmentation_narray = self.load_segmentation_as_narray(pair[1])
            segmentation_narray = segmentation_narray.astype(np.uint16)
            segmentation_narray3d = segmentation_narray[None, ...]
            # Load DICOM
            image_itk = sitk.ReadImage(pair[0])
            segmentation_itk = sitk.GetImageFromArray(segmentation_narray3d)
            segmentation_itk.CopyInformation(image_itk)
            segmentation_itk_name = os.path.split(pair[1])[1] + '.nii.gz'
            segmentation_itk_path = os.path.join(self.output(), segmentation_itk_name)
            sitk.WriteImage(segmentation_itk, segmentation_itk_path, useCompression=True)
            self.create_png_from_array(segmentation_narray, os.path.join(self.output(), segmentation_itk_name))
            self.create_png_from_dicom(pair[0])
            self.set_progress(step, nr_steps)