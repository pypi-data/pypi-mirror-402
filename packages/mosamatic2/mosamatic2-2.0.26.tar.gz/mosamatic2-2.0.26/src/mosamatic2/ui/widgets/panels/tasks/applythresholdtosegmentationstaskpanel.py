import os
import pathlib
import subprocess
import sys

from PySide6.QtWidgets import (
    QLineEdit,
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QHBoxLayout,
    QVBoxLayout,
    QFormLayout,
    QPushButton,
    QFileDialog,
    QMessageBox,
)
from PySide6.QtCore import (
    QThread, 
    Slot,
)

from mosamatic2.core.managers.logmanager import LogManager
from mosamatic2.ui.widgets.panels.tasks.taskpanel import TaskPanel
from mosamatic2.ui.settings import Settings
from mosamatic2.ui.utils import is_macos
from mosamatic2.ui.worker import Worker
from mosamatic2.core.tasks import ApplyThresholdToSegmentationsTask

LOG = LogManager()

PANEL_TITLE = 'ApplyThresholdToSegmentationsTask'
PANEL_NAME = 'applythresholdtosegmentationstaskpanel'


class ApplyThresholdToSegmentationsTaskPanel(TaskPanel):
    def __init__(self):
        super(ApplyThresholdToSegmentationsTaskPanel, self).__init__()
        self.set_title(PANEL_TITLE)
        self._images_dir_line_edit = None
        self._images_dir_select_button = None
        self._segmentations_dir_line_edit = None
        self._segmentations_dir_select_button = None
        self._output_dir_line_edit = None
        self._output_dir_select_button = None
        self._threshold_low_spinbox = None
        self._threshold_high_spinbox = None
        self._label_combobox = None
        self._overwrite_checkbox = None
        self._form_layout = None
        self._run_task_button = None
        self._open_excel_button = None
        self._settings = None
        self._task = None
        self._worker = None
        self._thread = None
        self.init_layout()

    def images_dir_line_edit(self):
        if not self._images_dir_line_edit:
            self._images_dir_line_edit = QLineEdit(self.settings().get(f'{PANEL_NAME}/images_dir'))
        return self._images_dir_line_edit
    
    def images_dir_select_button(self):
        if not self._images_dir_select_button:
            self._images_dir_select_button = QPushButton('Select')
            self._images_dir_select_button.clicked.connect(self.handle_images_dir_select_button)
        return self._images_dir_select_button
    
    def segmentations_dir_line_edit(self):
        if not self._segmentations_dir_line_edit:
            self._segmentations_dir_line_edit = QLineEdit(self.settings().get(f'{PANEL_NAME}/segmentations_dir'))
        return self._segmentations_dir_line_edit
    
    def segmentations_dir_select_button(self):
        if not self._segmentations_dir_select_button:
            self._segmentations_dir_select_button = QPushButton('Select')
            self._segmentations_dir_select_button.clicked.connect(self.handle_segmentations_dir_select_button)
        return self._segmentations_dir_select_button
    
    def output_dir_line_edit(self):
        if not self._output_dir_line_edit:
            self._output_dir_line_edit = QLineEdit(self.settings().get(f'{PANEL_NAME}/output_dir'))
        return self._output_dir_line_edit
    
    def output_dir_select_button(self):
        if not self._output_dir_select_button:
            self._output_dir_select_button = QPushButton('Select')
            self._output_dir_select_button.clicked.connect(self.handle_output_dir_select_button)
        return self._output_dir_select_button
    
    def threshold_low_spinbox(self):
        if not self._threshold_low_spinbox:
            self._threshold_low_spinbox = QDoubleSpinBox(minimum=-200, maximum=150, value=5)
            self._threshold_low_spinbox.setValue(self.settings().get_int(f'{PANEL_NAME}/threshold_low', 5))
        return self._threshold_low_spinbox
    
    def threshold_high_spinbox(self):
        if not self._threshold_high_spinbox:
            self._threshold_high_spinbox = QDoubleSpinBox(minimum=-200, maximum=150, value=150)
            self._threshold_high_spinbox.setValue(self.settings().get_int(f'{PANEL_NAME}/threshold_high', 150))
        return self._threshold_high_spinbox
    
    def label_combobox(self):
        if not self._label_combobox:
            self._label_combobox = QComboBox()
            self._label_combobox.addItems(['1', '5', '7'])
            self._label_combobox.setCurrentText(self.settings().get(f'{PANEL_NAME}/label', '1'))
        return self._label_combobox
    
    def overwrite_checkbox(self):
        if not self._overwrite_checkbox:
            self._overwrite_checkbox = QCheckBox('')
            self._overwrite_checkbox.setChecked(self.settings().get_bool(f'{PANEL_NAME}/overwrite', True))
        return self._overwrite_checkbox
    
    def form_layout(self):
        if not self._form_layout:
            self._form_layout = QFormLayout()
            if is_macos():
                self._form_layout.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
        return self._form_layout
    
    def run_task_button(self):
        if not self._run_task_button:
            self._run_task_button = QPushButton('Run task')
            self._run_task_button.clicked.connect(self.handle_run_task_button)
        return self._run_task_button
    
    def open_excel_button(self):
        if not self._open_excel_button:
            self._open_excel_button = QPushButton('Open output in Excel')
            self._open_excel_button.clicked.connect(self.handle_open_excel_button)
        return self._open_excel_button
    
    def settings(self):
        if not self._settings:
            self._settings = Settings()
        return self._settings
    
    def init_layout(self):
        images_dir_layout = QHBoxLayout()
        images_dir_layout.addWidget(self.images_dir_line_edit())
        images_dir_layout.addWidget(self.images_dir_select_button())
        segmentations_dir_layout = QHBoxLayout()
        segmentations_dir_layout.addWidget(self.segmentations_dir_line_edit())
        segmentations_dir_layout.addWidget(self.segmentations_dir_select_button())
        output_dir_layout = QHBoxLayout()
        output_dir_layout.addWidget(self.output_dir_line_edit())
        output_dir_layout.addWidget(self.output_dir_select_button())
        self.form_layout().addRow('Images directory', images_dir_layout)
        self.form_layout().addRow('Segmentations directory', segmentations_dir_layout)
        self.form_layout().addRow('Output directory', output_dir_layout)
        self.form_layout().addRow('Threshold low', self.threshold_low_spinbox())
        self.form_layout().addRow('Threshold high', self.threshold_high_spinbox())
        self.form_layout().addRow('Label', self.label_combobox())
        self.form_layout().addRow('Overwrite', self.overwrite_checkbox())
        layout = QVBoxLayout()
        layout.addLayout(self.form_layout())
        layout.addWidget(self.run_task_button())
        # layout.addWidget(self.open_excel_button())
        self.setLayout(layout)
        self.setObjectName(PANEL_NAME)

    def handle_images_dir_select_button(self):
        last_directory = self.settings().get('last_directory')
        directory = QFileDialog.getExistingDirectory(dir=last_directory)
        if directory:
            self.images_dir_line_edit().setText(directory)
            self.settings().set('last_directory', directory)

    def handle_segmentations_dir_select_button(self):
        last_directory = self.settings().get('last_directory')
        directory = QFileDialog.getExistingDirectory(dir=last_directory)
        if directory:
            self.segmentations_dir_line_edit().setText(directory)
            self.settings().set('last_directory', directory)

    def handle_output_dir_select_button(self):
        last_directory = self.settings().get('last_directory')
        directory = QFileDialog.getExistingDirectory(dir=last_directory)
        if directory:
            self.output_dir_line_edit().setText(directory)
            self.settings().set('last_directory', directory)

    def handle_run_task_button(self):
        errors = self.check_inputs_and_parameters()
        if len(errors) > 0:
            error_message = 'Following errors were encountered:\n'
            for error in errors:
                error_message += f' - {error}\n'
            QMessageBox.information(self, 'Error', error_message)
        else:
            LOG.info('Running task...')
            self.run_task_button().setEnabled(False)
            self.save_inputs_and_parameters()
            self._task = ApplyThresholdToSegmentationsTask(
                inputs={
                    'images': self.images_dir_line_edit().text(),
                    'segmentations': self.segmentations_dir_line_edit().text(),
                },
                params={
                    'label': int(self.label_combobox().currentText()),
                    'threshold_low': self.threshold_low_spinbox().value(),
                    'threshold_high': self.threshold_high_spinbox().value(),
                },
                output=self.output_dir_line_edit().text(),
                overwrite=self.overwrite_checkbox().isChecked(),
            )
            self._worker = Worker(self._task)
            self._thread = QThread()
            self._worker.moveToThread(self._thread)
            self._thread.started.connect(self._worker.run)
            self._worker.progress.connect(self.handle_progress)
            self._worker.status.connect(self.handle_status)
            self._worker.finished.connect(self.handle_finished)
            self._worker.finished.connect(self._thread.quit)
            self._worker.finished.connect(self._worker.deleteLater)
            self._thread.finished.connect(self._thread.deleteLater)
            self._thread.start()

    def handle_open_excel_button(self):
        file_path = os.path.join(self.output_dir_line_edit().text(), 'calculatescorestask', 'bc_scores.xlsx')
        file_path = pathlib.Path(file_path).expanduser().resolve()
        if not file_path.exists():
            raise FileNotFoundError(file_path)
        if sys.platform.startswith('win'):
            os.startfile(str(file_path))
        elif sys.platform == 'darwin':
            subprocess.run(['open', str(file_path)], check=True)
        else:
            subprocess.run(["xdg-open", str(file_path)], check=True)

    @Slot(int)
    def handle_progress(self, progress):
        LOG.info(f'Progress: {progress} / 100%')

    @Slot(str)
    def handle_status(self, status):
        LOG.info(f'Status: {status}')

    @Slot()
    def handle_finished(self):
        self.run_task_button().setEnabled(True)

    # HELPERS

    def check_inputs_and_parameters(self):
        errors = []
        if self.images_dir_line_edit().text() == '':
            errors.append('Empty images directory path')
        if not os.path.isdir(self.images_dir_line_edit().text()):
            errors.append('Images directory does not exist')
        if self.segmentations_dir_line_edit().text() == '':
            errors.append('Empty segmentations directory path')
        if not os.path.isdir(self.segmentations_dir_line_edit().text()):
            errors.append('Segmentations directory does not exist')
        if self.output_dir_line_edit().text() == '':
            errors.append('Empty output directory path')
        if os.path.isdir(self.output_dir_line_edit().text()) and not self.overwrite_checkbox().isChecked():
            errors.append('Output directory exists but overwrite=False. Please remove output directory first')
        return errors
    
    def save_inputs_and_parameters(self):
        self.settings().set(f'{PANEL_NAME}/images_dir', self.images_dir_line_edit().text())
        self.settings().set(f'{PANEL_NAME}/segmentations_dir', self.segmentations_dir_line_edit().text())
        self.settings().set(f'{PANEL_NAME}/output_dir', self.output_dir_line_edit().text())
        self.settings().set(f'{PANEL_NAME}/label', self.label_combobox().currentText())
        self.settings().set(f'{PANEL_NAME}/threshold_low', self.threshold_low_spinbox().value())
        self.settings().set(f'{PANEL_NAME}/threshold_high', self.threshold_high_spinbox().value())
        self.settings().set(f'{PANEL_NAME}/overwrite', self.overwrite_checkbox().isChecked())