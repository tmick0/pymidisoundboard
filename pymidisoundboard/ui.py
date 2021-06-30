

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
        main = self.parent().parent().parent().parent().parent().parent().parent()
        def on_note_cancel():
            main.cancel_intercept_next_note()
        dialog.canceled.connect(on_note_cancel)
        def on_note_receive(n):
            self.field['value'] = n
            self.spin.setValue(n)
            dialog.setValue(1)
        main.intercept_next_note(on_note_receive)
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


class msb_bank(qt.QWidget):
    def __init__(self, parent, config, bank):
        super().__init__(parent)
        self.config = config
        self.bank = bank
        self.initLayout()
        
    def initLayout(self):
        layout = qt.QGridLayout()
        for i in range(self.config.dict['ncol']):
            layout.setColumnStretch(i, self.config.dict['nrow'] - 1)
        for i in range(self.config.dict['ncol']*self.config.dict['nrow']):
            p = self.config.dict['banks'][self.bank]['pads'][i]
            widget = msb_pad(self, p)
            layout.addWidget(widget)
        self.setLayout(layout)


class msb_cc (qt.QWidget):
    def __init__(self, parent, bank, range=None):
        super().__init__(parent)
        self.bank = bank
        layout = qt.QVBoxLayout()
        self.spin = qt.QSpinBox()
        if range is not None:
            self.spin.setRange(*range)
        self.spin.setSingleStep(1)
        self.spin.setValue(bank['cc'])
        self.spin.valueChanged.connect(self.updated)
        layout.addWidget(self.spin)
        self.button = qt.QPushButton("Choose Bank Change CC", self)
        self.button.setToolTip("Set from MIDI")
        self.button.clicked.connect(self.on_button_click)
        layout.addWidget(self.button)
        self.setLayout(layout)
        
    def updated(self):
        self.bank['cc'] = self.spin.value()
    
    def on_button_click(self):
        dialog = qt.QProgressDialog("Waiting for MIDI CC", "Cancel", 0, 1, self)
        main = self.parent().parent().parent().parent().parent().parent()
        def on_cc_cancel():
            main.cancel_intercept_next_cc()
        dialog.canceled.connect(on_cc_cancel)
        def on_cc_receive(n):
            self.bank['cc'] = n
            self.spin.setValue(n)
            dialog.setValue(1)
        main.intercept_next_cc(on_cc_receive)
        dialog.show()


class msb_layout(qt.QWidget):
    def __init__(self, parent, config, bank):
        super().__init__(parent)
        self.config = config
        self.bank = bank
        self.bank_ui = msb_bank(self, config, bank)
        self.initLayout()
    
    def initLayout(self):
        layout = qt.QVBoxLayout()
        layout.addWidget(self.bank_ui)
        form = qt.QFormLayout()
        form.addRow(qt.QLabel("Bank Change CC"), msb_cc(self, self.config.dict['banks'][self.bank]))
        form_container = qt.QWidget()
        form_container.setLayout(form)
        layout.addWidget(form_container)
        self.setLayout(layout)


class msb_tabs(qt.QTabWidget):
    def __init__(self, parent, config):
        super().__init__(parent)
        self.config = config
        self.initLayout()
    
    def initLayout(self):
        if not 'nrow' in self.config.dict:
            self.config.dict['nrow'] = 2
        if not 'ncol' in self.config.dict:
            self.config.dict['ncol'] = 4
        if not 'nbanks' in self.config.dict:
            self.config.dict['nbanks'] = 1
        
        if not 'banks' in self.config.dict:
            self.config.dict['banks'] = []

        for i in range(self.config.dict['nbanks']):
            try:
                bank = self.config.dict['banks'][i]
                for j in range(self.config.dict['ncol'] * self.config.dict['nrow']):
                    try:
                        bank['pads'][j]
                    except IndexError:
                        bank['pads'].append({})
            except IndexError:
                self.config.dict['banks'].append({
                    'cc': 0,
                    'pads': [{} for i in range(self.config.dict['ncol'] * self.config.dict['nrow'])]
                })

        for i, b in enumerate(self.config.dict['banks']):
            self.addTab(msb_layout(self, self.config, i), "Bank {:d}".format(i+1))

    def update_ui(self, banks, rows, cols):
        self.clear()
        self.initLayout()


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


class msb_uiconfig_form (qt.QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        form = qt.QFormLayout()
        form.addRow(qt.QLabel("Banks"), parent.banks_spinner)
        form.addRow(qt.QLabel("Rows"), parent.rows_spinner)
        form.addRow(qt.QLabel("Columns"), parent.cols_spinner)
        self.setLayout(form)
        

class msb_uiconfig (qt.QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("Configure UI")
        buttons = qt.QDialogButtonBox(qt.QDialogButtonBox.Ok | qt.QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        self.banks_spinner = qt.QSpinBox()
        self.rows_spinner = qt.QSpinBox()
        self.cols_spinner = qt.QSpinBox()
        layout = qt.QVBoxLayout()
        layout.addWidget(msb_uiconfig_form(self))
        layout.addWidget(buttons)
        self.setLayout(layout)

    def set_banks(self, n):
        self.banks_spinner.setValue(n)

    def set_rows(self, n):
        self.rows_spinner.setValue(n)

    def set_cols(self, n):
        self.cols_spinner.setValue(n)

    def num_banks(self):
        return self.banks_spinner.value()

    def num_rows(self):
        return self.rows_spinner.value()

    def num_cols(self):
        return self.cols_spinner.value()


class msb_config(qt.QWidget):
    def __init__(self, parent, config):
        super().__init__(parent)
        self.config = config
        self.initLayout()
    
    def initLayout(self):
        layout = qt.QHBoxLayout()
        self.choose_port_button = qt.QPushButton("Choose MIDI Port", self)
        self.choose_port_button.clicked.connect(self.on_choose_port_click)
        self.config_gui_button = qt.QPushButton("Configure UI", self)
        self.config_gui_button.clicked.connect(self.on_config_gui_click)
        layout.addWidget(self.choose_port_button)
        layout.addWidget(self.config_gui_button)
        self.setLayout(layout)

    def on_config_gui_click(self):
        dialog = msb_uiconfig(self)
        dialog.set_rows(self.config.dict['nrow'])
        dialog.set_cols(self.config.dict['ncol'])
        dialog.set_banks(self.config.dict['nbanks'])
        if dialog.exec():
            self.config.dict['nbanks'] = dialog.num_banks()
            self.config.dict['nrow'] = dialog.num_rows()
            self.config.dict['ncol'] = dialog.num_cols()
            self.parent().tabs.update_ui(self.config.dict['nbanks'], self.config.dict['nrow'], self.config.dict['ncol'])
            self.config.dict['banks'] = self.config.dict['banks'][:self.config.dict['nbanks']]
            for b in self.config.dict['banks']:
                b['pads'] = b['pads'][:self.config.dict['nrow']*self.config.dict['ncol']]

    def on_choose_port_click(self):
        dialog = msb_midichoose(self)
        dialog.set_ports(midi_interface.get_interfaces())
        if dialog.exec():
            self.parent().parent().set_midi_port(dialog.selection())


class msb_main(qt.QWidget):
    def __init__(self, parent, config):
        super().__init__(parent)
        self.config = config
        self.tabs = msb_tabs(self, self.config)
        self.initLayout()

    def initLayout(self):
        layout = qt.QVBoxLayout()
        layout.addWidget(self.tabs)
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
            self.midi = midi_interface.get_worker(self.config.dict['port'], self._midi_note, self._midi_cc)
        else:
            self.midi = None

        self.audio = audio_interface()
        self.initWindow()

    def current_bank(self):
        return self.widget.tabs.currentIndex()

    def set_bank(self, bank):
        self.widget.tabs.setCurrentIndex(bank)

    def set_midi_port(self, port):
        if port is not None:
            if self.midi is not None:
                self.midi.stop()
            self.midi = midi_interface.get_worker(port, self._midi_note, self._midi_cc)
            self.config.dict['port'] = port

    def intercept_next_note(self, dest):
        def intercept(*args):
            dest(*args)
            if self.midi is not None:
                self.midi.set_note_dest(self._midi_note)
        if self.midi is not None:
            self.midi.set_note_dest(intercept)

    def cancel_intercept_next_note(self):
        if self.midi is not None:
            self.midi.set_note_dest(self._midi_note)

    def intercept_next_cc(self, dest):
        def intercept(*args):
            dest(*args)
            if self.midi is not None:
                self.midi.set_cc_dest(self._midi_cc)
        if self.midi is not None:
            self.midi.set_cc_dest(intercept)

    def cancel_intercept_next_cc(self):
        if self.midi is not None:
            self.midi.set_cc_dest(self._midi_cc)

    def _midi_note(self, e):
        for pad in self.config.dict['banks'][self.current_bank()]['pads']:
            if pad['note']['value'] == e and os.path.exists(pad['file']['value']):
                self.audio.play(pad['file']['value'])
                break

    def _midi_cc(self, e):
        for i, bank in enumerate(self.config.dict['banks']):
            if bank['cc'] == e:
                self.set_bank(i)
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
