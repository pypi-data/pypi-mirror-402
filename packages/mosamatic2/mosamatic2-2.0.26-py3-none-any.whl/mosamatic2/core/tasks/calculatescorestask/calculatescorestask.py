import os
import csv
import numpy as np
import pandas as pd
from mosamatic2.core.tasks.task import Task
from mosamatic2.core.managers.logmanager import LogManager
from mosamatic2.core.data.multidicomimage import MultiDicomImage
from mosamatic2.core.data.numpyimage import NumpyImage
from mosamatic2.core.utils import (
    get_pixels_from_dicom_object,
    calculate_area,
    calculate_index,
    calculate_bmi,
    calculate_sarcopenia,
    calculate_sarcopenic_obesity,
    calculate_myosteatosis,
    calculate_visceral_obesity,
    calculate_mean_radiation_attenuation,
    calculate_lama_percentage,
    get_pixels_from_tag_file,
    MUSCLE,
    SAT,
    VAT,
)

LOG = LogManager()


class CalculateScoresTask(Task):
    INPUTS = [
        'images', 
        'segmentations',
        'info',
    ]
    PARAMS = ['file_type']

    def __init__(self, inputs, params, output, overwrite=True):
        super(CalculateScoresTask, self).__init__(inputs, params, output, overwrite)

    def collect_img_seg_pairs(self, images, segmentations, file_type='npy'):
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

    def load_patient_info(self, f):
        columns = ['file', 'height', 'weight', 'sex', 'age']
        with open(f, mode='r', encoding='utf-8') as f_obj:
            reader = csv.DictReader(f_obj)
            if set(columns).issubset(reader.fieldnames):
                return [row for row in reader]
            LOG.error(f'Patient info CSV misses columns from {columns}')
        return None
        
    def get_patient_height(self, file_name, patient_info):
        for row in patient_info:
            if row['file'] in file_name:
                return float(row['height'])
        return None
    
    def get_patient_weight(self, file_name, patient_info):
        for row in patient_info:
            if row['file'] in file_name:
                return float(row['weight'])
        return None
    
    def get_patient_sex(self, file_name, patient_info) -> str:
        for row in patient_info:
            if row['file'] in file_name:
                if row['sex'] in ['male', 'female']:
                    return row['sex']
                else:
                    LOG.error(f'Sex should be either male or female in patient info CSV')
        return 'unknown'
    
    def get_patient_age(self, file_name, patient_info):
        for row in patient_info:
            if row['file'] in file_name:
                return float(row['age'])
        return None
    
    def run(self):
        image_data = self.load_images()
        images = image_data.images()
        file_type = self.param('file_type')
        segmentations = self.load_segmentations(file_type)
        img_seg_pairs = self.collect_img_seg_pairs(images, segmentations, file_type)
        patient_info = None
        patient_info_file = self.input('info')
        if patient_info_file:
            patient_info = self.load_patient_info(patient_info_file)
        # Create empty data dictionary
        data = {
            'file': [], 
            'muscle_area': [], 'muscle_idx': [], 'muscle_ra': [], 'muscle_lama_perc': [],
            'vat_area': [], 'vat_idx': [], 'vat_ra': [],
            'sat_area': [], 'sat_idx': [], 'sat_ra': [],
            'bmi': [],
            'sarcopenia': [],
            'sarcopenic_obesity': [],
            'myosteatosis': [],
            'visceral_obesity': [],
        }
        nr_steps = len(img_seg_pairs)
        for step in range(nr_steps):
            # Get image and its pixel spacing
            image, pixel_spacing = self.load_pixels_and_spacing(img_seg_pairs[step][0])
            if image is None:
                raise RuntimeError(f'Could not load DICOM image for file {img_seg_pairs[step][0]}')
            # Get segmentation for this image
            segmentation = self.load_segmentation(img_seg_pairs[step][1], file_type)
            if segmentation is None:
                LOG.warning(f'Could not load segmentation for file {img_seg_pairs[step][1]}')
                continue
            # Calculate metrics
            file_name = os.path.split(img_seg_pairs[step][0].path())[1]
            muscle_area = calculate_area(segmentation, MUSCLE, pixel_spacing)
            muscle_idx = 0
            if patient_info:
                muscle_idx = calculate_index(muscle_area, self.get_patient_height(file_name, patient_info))
            muscle_ra = calculate_mean_radiation_attenuation(image, segmentation, MUSCLE)
            muscle_lama_perc = calculate_lama_percentage(image, segmentation, MUSCLE)
            vat_area = calculate_area(segmentation, VAT, pixel_spacing)
            vat_idx = 0
            if patient_info:
                vat_idx = calculate_index(vat_area, self.get_patient_height(file_name, patient_info))
            vat_ra = calculate_mean_radiation_attenuation(image, segmentation, VAT)
            sat_area = calculate_area(segmentation, SAT, pixel_spacing)
            sat_idx = 0
            if patient_info:
                sat_idx = calculate_index(sat_area, self.get_patient_height(file_name, patient_info))
            sat_ra = calculate_mean_radiation_attenuation(image, segmentation, SAT)
            sex = 'unknown'
            if patient_info:
                sex = self.get_patient_sex(file_name, patient_info)
            bmi = 0
            if patient_info:
                bmi = calculate_bmi(
                    self.get_patient_weight(file_name, patient_info), 
                    self.get_patient_height(file_name, patient_info),
                )
            sarcopenia = 'no'
            if patient_info:
                sarcopenia = calculate_sarcopenia(muscle_idx, bmi, sex)
            sarcopenic_obesity = 'no'
            if patient_info:
                sarcopenic_obesity = calculate_sarcopenic_obesity(muscle_idx, bmi, sex)
            myosteatosis = 'no'
            if patient_info:
                myosteatosis = calculate_myosteatosis(muscle_ra, bmi)
            visceral_obesity = 'no'
            if patient_info:
                visceral_obesity = calculate_visceral_obesity(vat_area)
            LOG.info(f'file: {file_name}, ' +
                    f'muscle_area: {muscle_area}, muscle_idx: {muscle_idx}, muscle_ra: {muscle_ra}, ' +
                    f'vat_area: {vat_area}, vat_idx: {vat_idx}, vat_ra: {vat_ra}, ' +
                    f'sat_area: {sat_area}, sat_idx: {sat_idx}, sat_ra: {sat_ra}, ' +
                    f'muscle_lama_perc: {muscle_lama_perc}, ' +
                    f'bmi: {bmi}, ' +
                    f'sarcopenia: {sarcopenia}, ' +
                    f'sarcopenic_obesity: {sarcopenic_obesity}, ' +
                    f'myosteatosis: {myosteatosis}, ' +
                    f'visceral_obesity: {visceral_obesity}'
            )
            # Update dataframe data
            data['file'].append(file_name)
            data['muscle_area'].append(muscle_area)
            data['muscle_idx'].append(muscle_idx)
            data['muscle_ra'].append(muscle_ra)
            data['muscle_lama_perc'].append(muscle_lama_perc)
            data['vat_area'].append(vat_area)
            data['vat_idx'].append(vat_idx)
            data['vat_ra'].append(vat_ra)
            data['sat_area'].append(sat_area)
            data['sat_idx'].append(sat_idx)
            data['sat_ra'].append(sat_ra)
            data['bmi'].append(bmi)
            data['sarcopenia'].append(sarcopenia)
            data['sarcopenic_obesity'].append(sarcopenic_obesity)
            data['myosteatosis'].append(myosteatosis)
            data['visceral_obesity'].append(visceral_obesity)
            # Update progress
            self.set_progress(step, nr_steps)
        # Build dataframe and return the CSV file as output
        csv_file_path = os.path.join(self.output(), 'bc_scores.csv')
        xls_file_path = os.path.join(self.output(), 'bc_scores.xlsx')
        df = pd.DataFrame(data=data)
        df.to_csv(csv_file_path, index=False, sep=';')
        df.to_excel(xls_file_path, index=False, engine='openpyxl')