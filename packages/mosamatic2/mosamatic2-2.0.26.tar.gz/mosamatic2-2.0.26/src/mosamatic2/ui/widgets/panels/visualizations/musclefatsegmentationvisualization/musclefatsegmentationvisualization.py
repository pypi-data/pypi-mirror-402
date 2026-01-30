from PySide6.QtWidgets import (
    QLineEdit,
    QHBoxLayout,
    QVBoxLayout,
    QFormLayout,
    QPushButton,
    QFileDialog,
    QLabel,
    QSlider,
)
from PySide6.QtCore import Qt
from mosamatic2.ui.widgets.panels.visualizations.visualization import Visualization
from mosamatic2.ui.widgets.panels.visualizations.musclefatsegmentationvisualization.musclefatsegmentationviewer import MuscleFatSegmentationViewer
from mosamatic2.core.managers.logmanager import LogManager
from mosamatic2.ui.settings import Settings
from mosamatic2.ui.utils import is_macos

LOG = LogManager()
PANEL_TITLE = 'MuscleFatSegmentationVisualization'
PANEL_NAME = 'musclefatsegmentationvisualization'


class MuscleFatSegmentationVisualization(Visualization):
    def __init__(self):
        super(MuscleFatSegmentationVisualization, self).__init__()
        self.set_title(PANEL_TITLE)
        self._images_line_edit = None
        self._image_file_select_button = None
        self._segmentation_line_edit = None
        self._segmentation_file_select_button = None
        self._load_data_button = None
        self._lo_slider_value_label = None
        self._lo_slider = None
        self._hi_slider_value_label = None
        self._hi_slider = None
        self._muscle_fat_segmentation_viewer = None
        self._form_layout = None
        self._settings = None
        self.init_layout()

    def image_line_edit(self):
        if not self._images_line_edit:
            self._images_line_edit = QLineEdit(self.settings().get(f'{PANEL_NAME}/image'))
        return self._images_line_edit
    
    def image_file_select_button(self):
        if not self._image_file_select_button:
            self._image_file_select_button = QPushButton('Select file')
            self._image_file_select_button.clicked.connect(self.handle_image_file_select_button)
        return self._image_file_select_button
    
    def segmentation_line_edit(self):
        if not self._segmentation_line_edit:
            self._segmentation_line_edit = QLineEdit(self.settings().get(f'{PANEL_NAME}/segmentation'))
        return self._segmentation_line_edit
    
    def segmentation_file_select_button(self):
        if not self._segmentation_file_select_button:
            self._segmentation_file_select_button = QPushButton('Select file')
            self._segmentation_file_select_button.clicked.connect(self.handle_segmentation_file_select_button)
        return self._segmentation_file_select_button
    
    def load_data_button(self):
        if not self._load_data_button:
            self._load_data_button = QPushButton('Load')
            self._load_data_button.clicked.connect(self.handle_load_data_button)
        return self._load_data_button
    
    def lo_slider_value_label(self):
        if not self._lo_slider_value_label:
            self._lo_slider_value_label = QLabel('')
        return self._lo_slider_value_label
    
    def lo_slider(self):
        if not self._lo_slider:
            self._lo_slider = QSlider(Qt.Horizontal)
            self._lo_slider.setRange(-29, 150)
            self._lo_slider.setValue(30)
            self._lo_slider.valueChanged.connect(self.handle_lo_slider)
            self.lo_slider_value_label().setText(str(30))
        return self._lo_slider
    
    def hi_slider_value_label(self):
        if not self._hi_slider_value_label:
            self._hi_slider_value_label = QLabel('')
        return self._hi_slider_value_label
    
    def hi_slider(self):
        if not self._hi_slider:
            self._hi_slider = QSlider(Qt.Horizontal)
            self._hi_slider.setRange(-29, 150)
            self._hi_slider.setValue(150)
            self._hi_slider.valueChanged.connect(self.handle_hi_slider)
            self.hi_slider_value_label().setText(str(150))
        return self._hi_slider
    
    def muscle_fat_segmentation_viewer(self):
        if not self._muscle_fat_segmentation_viewer:
            self._muscle_fat_segmentation_viewer = MuscleFatSegmentationViewer()
        return self._muscle_fat_segmentation_viewer
    
    def form_layout(self):
        if not self._form_layout:
            self._form_layout = QFormLayout()
            if is_macos():
                self._form_layout.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
        return self._form_layout

    def settings(self):
        if not self._settings:
            self._settings = Settings()
        return self._settings

    def init_layout(self):
        image_layout = QHBoxLayout()
        image_layout.addWidget(self.image_line_edit())
        image_layout.addWidget(self.image_file_select_button())
        segmentation_layout = QHBoxLayout()
        segmentation_layout.addWidget(self.segmentation_line_edit())
        segmentation_layout.addWidget(self.segmentation_file_select_button())
        lo_slider_layout = QHBoxLayout()
        lo_slider_layout.addWidget(self.lo_slider_value_label())
        lo_slider_layout.addWidget(self.lo_slider())
        hi_slider_layout = QHBoxLayout()
        hi_slider_layout.addWidget(self.hi_slider_value_label())
        hi_slider_layout.addWidget(self.hi_slider())
        self.form_layout().addRow('Image file', image_layout)
        self.form_layout().addRow('Segmentation file', segmentation_layout)
        self.form_layout().addRow('', lo_slider_layout)
        self.form_layout().addRow('', hi_slider_layout)
        layout = QVBoxLayout()
        layout.addLayout(self.form_layout())
        layout.addWidget(self.load_data_button())
        layout.addWidget(self.muscle_fat_segmentation_viewer().navigation_toolbar())
        layout.addWidget(self.muscle_fat_segmentation_viewer())
        self.setLayout(layout)
        self.setObjectName(PANEL_NAME)

    def handle_image_file_select_button(self):
        last_directory = self.settings().get('last_directory')
        file_path, _ = QFileDialog.getOpenFileName(dir=last_directory)
        if file_path:
            self.image_line_edit().setText(file_path)
            self.settings().set('last_directory', file_path)

    def handle_segmentation_file_select_button(self):
        last_directory = self.settings().get('last_directory')
        file_path, _ = QFileDialog.getOpenFileName(dir=last_directory)
        if file_path:
            self.segmentation_line_edit().setText(file_path)
            self.settings().set('last_directory', file_path)

    def handle_load_data_button(self):
        self.muscle_fat_segmentation_viewer().load_data(
            self.image_line_edit().text(),
            self.segmentation_line_edit().text(),
            lo_hu=self.lo_slider().value(),
            hi_hu=self.hi_slider().value(),
        )

    def handle_lo_slider(self, value):
        self.muscle_fat_segmentation_viewer().update_lo_hu(value)
        self.lo_slider_value_label().setText(str(value))

    def handle_hi_slider(self, value):
        self.muscle_fat_segmentation_viewer().update_hi_hu(value)
        self.hi_slider_value_label().setText(str(value))

    def save_inputs_and_parameters(self):
        self.settings().set(f'{PANEL_NAME}/image', self.image_line_edit().text())
        self.settings().set(f'{PANEL_NAME}/segmentation', self.segmentation_line_edit().text())