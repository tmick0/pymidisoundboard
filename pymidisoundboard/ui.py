

from PyQt5 import QtWidgets as qt
from PyQt5.QtCore import QObject, QThread, pyqtSignal

from .midi import midi_interface
from .audio import audio_interface
from .config import config

import os


class msb_note (qt.QWidget):
    def __init__(self, parent, field, range=None):
        super().__init__(parent)
        self.field = field
        if not 'value' in field:
            field['value'] = 0
        layout = qt.QVBoxLayout()
        self.spin = qt.QSpinBox()
        if range is not None:
            self.spin.setRange(*range)
        self.spin.setSingleStep(1)
        self.spin.setValue(field['value'])
        self.spin.valueChanged.connect(self.updated)
        layout.addWidget(self.spin)
        self.button = qt.QPushButton("Choose Note", self)
        self.button.setToolTip("Set from MIDI")
        self.button.clicked.connect(self.on_button_click)
        layout.addWidget(self.button)
        self.setLayout(layout)
        
    def updated(self):
        self.field['value'] = self.spin.value()
    
    def on_button_click(self):
        dialog = qt.QProgressDialog("Waiting for MIDI note", "Cancel", 0, 1, self)
        def on_note_cancel():
            main = self.parent().parent().parent().parent()
            main.cancel_intercept_next_midi()
        dialog.canceled.connect(on_note_cancel)
        def on_note_receive(n):
            self.field['value'] = n
            self.spin.setValue(n)
            dialog.setValue(1)
        self.parent().parent().parent().parent().intercept_next_midi(on_note_receive)
        dialog.show()


class msb_file (qt.QWidget):
    def __init__(self, parent, field):
        super().__init__(parent)
        self.field = field
        if not 'value' in field:
            field['value'] = '(none)'
        layout = qt.QVBoxLayout()
        self.label = qt.QLabel(os.path.basename(self.field['value']))
        layout.addWidget(self.label)
        self.button = qt.QPushButton("Choose Clip", self)
        self.button.setToolTip("Choose audio file")
        self.button.clicked.connect(self.on_button_click)
        layout.addWidget(self.button)
        self.setLayout(layout)

    def on_button_click(self):
        options = qt.QFileDialog.Options()
        options |= qt.QFileDialog.DontUseNativeDialog
        dialog = qt.QFileDialog(self)
        dialog.setOptions(options)
        dialog.setNameFilter("Audio Files (*.mp3 *.wav);;All Files (*)")
        dialog.setFileMode(qt.QFileDialog.ExistingFile)
        dialog.setAcceptMode(qt.QFileDialog.AcceptOpen)
        dialog.fileSelected.connect(self.on_file_chosen)
        dialog.exec()

    def on_file_chosen(self, filename):
        if filename:
            self.field['value'] = filename
            self.label.setText(os.path.basename(filename))


class msb_pad (qt.QGroupBox):
    def __init__(self, parent, pad):
        super().__init__(parent)
        self.pad = pad
        self.initLayout()
    
    def initLayout(self):
        layout = qt.QFormLayout()
        if not 'note' in self.pad:
            self.pad['note'] = {}
        if not 'file' in self.pad:
            self.pad['file'] = {}
        layout.addRow(qt.QLabel("Note"), msb_note(self, self.pad['note']))
        layout.addRow(qt.QLabel("File"), msb_file(self, self.pad['file']))
        self.setLayout(layout)


class msb_layout(qt.QWidget):
    def __init__(self, parent, config):
        super().__init__(parent)
        self.config = config
        self.initLayout()
    
    def initLayout(self):
        layout = qt.QGridLayout()

        if not 'nrow' in self.config.dict:
            self.config.dict['nrow'] = 2
        if not 'ncol' in self.config.dict:
            self.config.dict['ncol'] = 4

        for i in range(self.config.dict['ncol']):
            layout.setColumnStretch(i, self.config.dict['nrow'] - 1)
        
        if not 'pads' in self.config.dict:
            self.config.dict['pads'] = [{} for i in range(self.config.dict['ncol'] * self.config.dict['nrow'])]

        for p in self.config.dict['pads']:
            widget = msb_pad(self, p)
            layout.addWidget(widget)

        self.setLayout(layout)


class msb_midichoose(qt.QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("Choose MIDI Port")
        buttons = qt.QDialogButtonBox(qt.QDialogButtonBox.Ok | qt.QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout = qt.QVBoxLayout()
        self.list = qt.QListWidget(self)
        layout.addWidget(self.list)
        layout.addWidget(buttons)
        self.setLayout(layout)
    
    def set_ports(self, ports):
        for port in ports:
            self.list.addItem(port)

    def selection(self):
        try:
            return self.list.selectedItems()[0].text()
        except IndexError:
            return None


class msb_config(qt.QWidget):
    def __init__(self, parent, config):
        super().__init__(parent)
        self.config = config
        self.initLayout()
    
    def initLayout(self):
        layout = qt.QHBoxLayout()
        self.button = qt.QPushButton("Choose MIDI Port", self)
        self.button.clicked.connect(self.on_click)
        layout.addWidget(self.button)
        self.setLayout(layout)

    def on_click(self):
        dialog = msb_midichoose(self)
        dialog.set_ports(midi_interface.get_interfaces())
        if dialog.exec():
            self.parent().parent().set_midi_port(dialog.selection())


class msb_main(qt.QWidget):
    def __init__(self, parent, config):
        super().__init__(parent)
        self.config = config
        self.initLayout()

    def initLayout(self):
        layout = qt.QVBoxLayout()
        layout.addWidget(msb_layout(self, self.config))
        layout.addWidget(msb_config(self, self.config))
        self.setLayout(layout)


class msb_ui (qt.QMainWindow):
    def __init__(self):
        super().__init__()
        self.config = config.load()

        if not 'port' in self.config.dict:
            try:
                self.config.dict['port'] = midi_interface.get_interfaces()[0]
            except IndexError:
                self.config.dict['port'] = None

        if self.config.dict['port'] is not None:
            self.midi = midi_interface.get_worker(self.config.dict['port'], self._midi_event)
        else:
            self.midi = None

        self.audio = audio_interface()
        self.initWindow()

    def set_midi_port(self, port):
        if port is not None:
            if self.midi is not None:
                self.midi.stop()
            self.midi = midi_interface.get_worker(port, self._midi_event)
            self.config.dict['port'] = port

    def intercept_next_midi(self, dest):
        def intercept(*args):
            dest(*args)
            if self.midi is not None:
                self.midi.set_event_dest(self._midi_event)
        if self.midi is not None:
            self.midi.set_event_dest(intercept)

    def cancel_intercept_next_midi(self):
        if self.midi is not None:
            self.midi.set_event_dest(self._midi_event)

    def _midi_event(self, e):
        for pad in self.config.dict['pads']:
            if pad['note']['value'] == e and os.path.exists(pad['file']['value']):
                self.audio.play(pad['file']['value'])
                break

    def initWindow(self):
        self.setWindowTitle('midi soundboard')
        self.initWidget()
        self.show()

    def initWidget(self):
        self.widget = msb_main(self, self.config)
        self.setCentralWidget(self.widget)
    
    def closeEvent(self, event):
        self.config.save()
        self.midi.stop()
