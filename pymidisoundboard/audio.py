import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GObject

class audio_interface (object):
    def __init__(self):
        self._player = Gst.Pipeline.new("pymidisoundboard")
        self._source = Gst.ElementFactory.make("filesrc", "source")
        decoder = Gst.ElementFactory.make("decodebin", "decode")
        conv = Gst.ElementFactory.make("audioconvert", "convert")
        self._sink = Gst.ElementFactory.make("autoaudiosink", "output")

        self._player.add(self._source)
        self._player.add(decoder)
        self._player.add(conv)
        self._player.add(self._sink)
        self._source.link(decoder)
            
        decoder.connect("pad-added", self._pad_added)

        bus = self._player.get_bus()
        bus.add_signal_watch()
        bus.connect("message", self._gst_message)

    def _pad_added(self, element, pad):
        pad.link(self._sink.get_static_pad("sink"))
    
    def _gst_message(self, bus, message):
        t = message.type
        if t == Gst.MessageType.EOS:
            self._player.set_state(Gst.State.NULL)
        elif t == Gst.MessageType.ERROR:
            print("{}: {}".format(message.src.name, message.get_structure().get_string("debug")))
            self._player.set_state(Gst.State.NULL)

    def play(self, file):
        self._player.set_state(Gst.State.NULL)
        self._source.set_property("location", file)
        self._player.set_state(Gst.State.PLAYING)
