from pkg_resources import parse_version
from kaitaistruct import __version__ as ks_version, KaitaiStruct, KaitaiStream, BytesIO
# This is a generated file! Please edit source .ksy file and use kaitai-struct-compiler to rebuild



if parse_version(ks_version) < parse_version('0.7'):
    raise Exception("Incompatible Kaitai Struct Python API: 0.7 or later is required, but you have %s" % (ks_version))

class Roh(KaitaiStruct):
    def __init__(self, _io, _parent=None, _root=None):
        self._io = _io
        self._parent = _parent
        self._root = _root if _root else self
        self.unknown1 = self._io.read_f4le()
        self.wlintercept = self._io.read_f4le()
        self.wlx1 = self._io.read_f4le()
        self.wlx2 = self._io.read_f4le()
        self.wlx3 = self._io.read_f4le()
        self.wlx4 = self._io.read_f4le()
        self.unknown2 = [None] * (9)
        for i in range(9):
            self.unknown2[i] = self._io.read_f4le()

        self.ipixfirst = self._io.read_f4le()
        self.ipixlast = self._io.read_f4le()
        self.unknown3 = [None] * (4)
        for i in range(4):
            self.unknown3[i] = self._io.read_f4le()

        self.spectrum = [None] * (((int(self.ipixlast) - int(self.ipixfirst)) - 1))
        for i in range(((int(self.ipixlast) - int(self.ipixfirst)) - 1)):
            self.spectrum[i] = self._io.read_f4le()

        self.integration_ms = self._io.read_f4le()
        self.averaging = self._io.read_f4le()
        self.pixel_smoothing = self._io.read_f4le()


