from PySide6.QtWidgets import (
    QTextEdit,
)
from mosamatic2.ui.widgets.panels.defaultpanel import DefaultPanel
from mosamatic2.core.managers.logmanager import LogManager

LOG = LogManager()

PANEL_TITLE = 'SettingsPanel'
PANEL_NAME = 'settingspanel'


class SettingsPanel(DefaultPanel):
    def __init__(self):
        super(SettingsPanel, self).__init__()
        self.set_title(PANEL_TITLE)