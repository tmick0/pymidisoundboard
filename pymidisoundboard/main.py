import sys

import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst

from PyQt5.QtWidgets import QApplication

from .ui import msb_ui

def main():
    Gst.init(sys.argv)
    app = QApplication(sys.argv)
    ex = msb_ui()
    sys.exit(app.exec_())
