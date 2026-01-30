import os
import numpy as np
import nibabel as nib
import matplotlib.pyplot as plt
from mosamatic2.core.tasks.task import Task
from mosamatic2.core.managers.logmanager import LogManager
from mosamatic2.core.utils import (
    convert_numpy_array_to_png_image,
    AlbertaColorMap, 
)
LOG = LogManager()


class SegmentationNifti2NumpyTask(Task):
    INPUTS = ['segmentations']
    PARAMS = ['png']

    def __init__(self, inputs, params, output, overwrite):
        super(SegmentationNifti2NumpyTask, self).__init__(inputs, params, output, overwrite)

    def load_segmentations(self):
        segmentations = []
        for f in os.listdir(self.input('segmentations')):
            if f.endswith('.seg.npy.nii.gz'):
                f_path = os.path.join(self.input('segmentations'), f)
                segmentations.append(f_path)
        return segmentations
    
    def load_segmentation_as_nifti(self, segmentation):
        nifti = nib.load(segmentation)
        narray = np.asanyarray(nifti.dataobj)
        narray = narray[..., 0]
        narray = np.rot90(narray, k=3, axes=(0, 1))
        return narray
    
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
        segmentations = self.load_segmentations()        
        nr_steps = len(segmentations)
        for step in range(nr_steps):
            segmentation = segmentations[step]
            segmentation_narray = self.load_segmentation_as_nifti(segmentation)
            segmentation_narray_name = os.path.split(segmentation)[1][:-7]
            segmentation_narray_path = os.path.join(self.output(), segmentation_narray_name)
            np.save(segmentation_narray_path, segmentation_narray)
            if self.param('png'):
                self.create_png_from_array(segmentation_narray, segmentation_narray_path)
            self.set_progress(step, nr_steps)