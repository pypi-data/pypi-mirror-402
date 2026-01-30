import os
import pandas as pd
from mosamatic2.core.tasks.task import Task
from mosamatic2.core.managers.logmanager import LogManager
from mosamatic2.core.utils import (
    is_dicom, 
    load_dicom,
    current_time_in_seconds,
    elapsed_time_in_seconds,
    duration,
)

LOG = LogManager()


class CreateDicomSummaryTask(Task):
    INPUTS = ['directory']
    PARAMS = []

    def __init__(self, inputs, params, output, overwrite):
        super(CreateDicomSummaryTask, self).__init__(inputs, params, output, overwrite)

    def get_values(self, files, tag_name):
        values = []
        for f in files:
            if tag_name in f.keys():
                if f[tag_name] not in values:
                    values.append(f[tag_name])
        return values
    
    def get_tag_value(self, p, tag_name):
        return p.data_element(tag_name).value
    
    def run(self):
        series = {}
        start_time = current_time_in_seconds()
        for root, dirs, files in os.walk(self.input('directory')):
            for f in files:
                f_path = os.path.join(root, f)
                if is_dicom(f_path):
                    p = load_dicom(f_path, stop_before_pixels=True)
                    if p:
                        patient_id = self.get_tag_value(p, 'PatientID')
                        if patient_id:
                            if patient_id not in series.keys():
                                series[patient_id] = {}
                            series_instance_uid = self.get_tag_value(p, 'SeriesInstanceUID')
                            if series_instance_uid:
                                if series_instance_uid not in series[patient_id].keys():
                                    series[patient_id][series_instance_uid] = []
                                series[patient_id][series_instance_uid].append({
                                    'series_description': self.get_tag_value(p, 'SeriesDescription'),
                                    'slice_thickness': self.get_tag_value(p, 'SliceThickness'),
                                    'rows': self.get_tag_value(p, 'Rows'),
                                    'columns': self.get_tag_value(p, 'Columns'),
                                    'pixel_spacing': self.get_tag_value(p, 'PixelSpacing'),
                                    'modality': self.get_tag_value(p, 'Modality'),
                                    'image_type': self.get_tag_value(p, 'ImageType'),
                                })
        data = {
            'patient_id': [],
            'series_description': [],
            'nr_images': [],
            'slice_thickness': [],
            'rows': [],
            'columns': [],
            'pixel_spacing': [],
            'modality': [],
            'image_type': [],
            'series_instance_uid': [],
        }
        for patient_id, v1 in series.items():
            for series_instance_uid, v2 in v1.items():
                data['patient_id'].append(patient_id)
                data['series_description'].append(self.get_values(v2, tag_name='series_description'))
                data['nr_images'].append(len(v2))
                data['slice_thickness'].append(self.get_values(v2, tag_name='slice_thickness'))
                data['rows'].append(self.get_values(v2, tag_name='rows'))
                data['columns'].append(self.get_values(v2, tag_name='columns'))
                data['pixel_spacing'].append(self.get_values(v2, tag_name='pixel_spacing'))
                data['modality'].append(self.get_values(v2, tag_name='modality'))
                data['image_type'].append(self.get_values(v2, tag_name='image_type'))
                data['series_instance_uid'].append(series_instance_uid)
        df = pd.DataFrame(data=data)
        df.to_csv(os.path.join(self.output(), 'summary.csv'), index=False, sep=';')
        df.to_excel(os.path.join(self.output(), 'summary.xlsx'), index=False, engine='openpyxl')
        LOG.info(df)
        LOG.info(f'Elapsed time: {duration(elapsed_time_in_seconds(start_time))}')