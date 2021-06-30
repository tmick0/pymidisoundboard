
import time
import mido
from PyQt5.QtCore import QObject, QThread, pyqtSignal

class midi_worker (QObject):
    midi_cc = pyqtSignal(int)
    midi_note = pyqtSignal(int)
    finished = pyqtSignal()

    def __init__(self, midi_port, parent=None):
        super().__init__(parent)
        self._port = midi_port
        self._running = True

    def stop_midi(self):
        self._running = False

    def run(self):
        input = mido.open_input(self._port)
        while self._running:
            e = input.poll()
            if e is not None:
                self._send_midi_event(e)
            time.sleep(0.01)
        self.finished.emit()
            
    def _send_midi_event(self, e):
        if e.type == 'note_on':
            self.midi_note.emit(e.note)
        elif e.type == 'control_change' and e.value > 0:
            self.midi_cc.emit(e.control)

class midi_interface (object):
    def __init__(self, thread, worker):
        self.thread = thread
        self.worker = worker
        thread.start()

    def set_note_dest(self, dest):
        self.worker.midi_note.disconnect()
        self.worker.midi_note.connect(dest)

    def set_cc_dest(self, dest):
        self.worker.midi_cc.disconnect()
        self.worker.midi_cc.connect(dest)

    def stop(self):
        self.worker.stop_midi()
        self.thread.quit()
        self.thread.wait()

    @classmethod
    def get_interfaces(cls):
        return mido.get_input_names()

    @classmethod
    def get_worker(cls, port, note_callback, cc_callback):
        thread = QThread()
        worker = midi_worker(port)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        worker.midi_note.connect(note_callback)
        worker.midi_cc.connect(cc_callback)
        return cls(thread, worker)
