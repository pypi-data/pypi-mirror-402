# This is a generated file! Please edit source .ksy file and use kaitai-struct-compiler to rebuild

import kaitaistruct
from kaitaistruct import KaitaiStruct, KaitaiStream, BytesIO


if getattr(kaitaistruct, 'API_VERSION', (0, 9)) < (0, 9):
    raise Exception("Incompatible Kaitai Struct Python API: 0.9 or later is required, but you have %s" % (kaitaistruct.__version__))

class Silversat(KaitaiStruct):
    """:field cw_callsign: silversat.cw_or_ssdv.cw_callsign
    :field power: silversat.cw_or_ssdv.power
    :field avionics: silversat.cw_or_ssdv.avionics
    :field payload: silversat.cw_or_ssdv.payload
    :field radio: silversat.cw_or_ssdv.radio
    :field cw_beacon: silversat.cw_or_ssdv.cw_beacon
    :field dest_callsign: silversat.cw_or_ssdv.ax25_frame.ax25_header.dest_callsign_raw.callsign_ror.callsign
    :field src_callsign: silversat.cw_or_ssdv.ax25_frame.ax25_header.src_callsign_raw.callsign_ror.callsign
    :field src_ssid: silversat.cw_or_ssdv.ax25_frame.ax25_header.src_ssid_raw.ssid
    :field dest_ssid: silversat.cw_or_ssdv.ax25_frame.ax25_header.dest_ssid_raw.ssid
    :field ctl: silversat.cw_or_ssdv.ax25_frame.ax25_header.ctl
    :field pid: silversat.cw_or_ssdv.ax25_frame.ax25_header.pid
    :field ssdv_sync_byte: silversat.cw_or_ssdv.ax25_frame.ax25_info.ssdv_sync_byte
    :field ssdv_packet_type: silversat.cw_or_ssdv.ax25_frame.ax25_info.ssdv_packet_type
    :field ssdv_callsign: silversat.cw_or_ssdv.ax25_frame.ax25_info.ssdv_callsign
    :field ssdv_image_id: silversat.cw_or_ssdv.ax25_frame.ax25_info.ssdv_image_id
    :field ssdv_packet_id: silversat.cw_or_ssdv.ax25_frame.ax25_info.ssdv_packet_id
    :field ssdv_width: silversat.cw_or_ssdv.ax25_frame.ax25_info.ssdv_width
    :field ssdv_height: silversat.cw_or_ssdv.ax25_frame.ax25_info.ssdv_height
    :field ssdv_flags: silversat.cw_or_ssdv.ax25_frame.ax25_info.ssdv_flags
    :field ssdv_mcu_offset: silversat.cw_or_ssdv.ax25_frame.ax25_info.ssdv_mcu_offset
    :field ssdv_mcu_index: silversat.cw_or_ssdv.ax25_frame.ax25_info.ssdv_mcu_index
    :field ssdv_image: silversat.cw_or_ssdv.ax25_frame.ax25_info.ssdv_image
    
    .. seealso::
       Source - https://github.com/silver-sat/systems/wiki/Beacon-Operations
    """
    def __init__(self, _io, _parent=None, _root=None):
        self._io = _io
        self._parent = _parent
        self._root = _root if _root else self
        self._read()

    def _read(self):
        self.silversat = Silversat.SilversatT(self._io, self, self._root)

    class SilversatT(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            _on = self.cw_or_ssdv_switch_on
            if _on == 2003841656:
                self.cw_or_ssdv = Silversat.Cw(self._io, self, self._root)
            else:
                self.cw_or_ssdv = Silversat.Ssdv(self._io, self, self._root)

        @property
        def cw_or_ssdv_switch_on(self):
            if hasattr(self, '_m_cw_or_ssdv_switch_on'):
                return self._m_cw_or_ssdv_switch_on

            _pos = self._io.pos()
            self._io.seek(0)
            self._m_cw_or_ssdv_switch_on = self._io.read_u4be()
            self._io.seek(_pos)
            return getattr(self, '_m_cw_or_ssdv_switch_on', None)


    class Cw(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.cw_callsign = (self._io.read_bytes(7)).decode(u"ASCII")
            if not self.cw_callsign == u"wp2xgw ":
                raise kaitaistruct.ValidationNotEqualError(u"wp2xgw ", self.cw_callsign, self._io, u"/types/cw/seq/0")
            self.power = (self._io.read_bytes(1)).decode(u"ASCII")
            if not  ((self.power == u"s") or (self.power == u"e") or (self.power == u"i") or (self.power == u"t") or (self.power == u"a")) :
                raise kaitaistruct.ValidationNotAnyOfError(self.power, self._io, u"/types/cw/seq/1")
            self.avionics = (self._io.read_bytes(1)).decode(u"ASCII")
            if not  ((self.avionics == u"e") or (self.avionics == u"s") or (self.avionics == u"a") or (self.avionics == u"h") or (self.avionics == u"n") or (self.avionics == u"u") or (self.avionics == u"i") or (self.avionics == u"d") or (self.avionics == u"r") or (self.avionics == u"t") or (self.avionics == u"5")) :
                raise kaitaistruct.ValidationNotAnyOfError(self.avionics, self._io, u"/types/cw/seq/2")
            self.payload = (self._io.read_bytes(1)).decode(u"ASCII")
            if not  ((self.payload == u"e") or (self.payload == u"i") or (self.payload == u"v") or (self.payload == u"w") or (self.payload == u"l") or (self.payload == u"5") or (self.payload == u"a") or (self.payload == u"h") or (self.payload == u"m") or (self.payload == u"4") or (self.payload == u"6") or (self.payload == u"c") or (self.payload == u"b") or (self.payload == u"s") or (self.payload == u"t") or (self.payload == u"n") or (self.payload == u"r") or (self.payload == u"u") or (self.payload == u"d") or (self.payload == u"f") or (self.payload == u"g") or (self.payload == u"k") or (self.payload == u"o") or (self.payload == u"7") or (self.payload == u"x") or (self.payload == u"z") or (self.payload == u"p") or (self.payload == u"3") or (self.payload == u"j") or (self.payload == u"q") or (self.payload == u"9") or (self.payload == u"0")) :
                raise kaitaistruct.ValidationNotAnyOfError(self.payload, self._io, u"/types/cw/seq/3")
            self.radio = (self._io.read_bytes(1)).decode(u"ASCII")
            if not  ((self.radio == u"e") or (self.radio == u"i") or (self.radio == u"s") or (self.radio == u"t") or (self.radio == u"n") or (self.radio == u"a") or (self.radio == u"h") or (self.radio == u"d") or (self.radio == u"r") or (self.radio == u"u") or (self.radio == u"5") or (self.radio == u"b") or (self.radio == u"v") or (self.radio == u"f") or (self.radio == u"l") or (self.radio == u"m") or (self.radio == u"4") or (self.radio == u"g")) :
                raise kaitaistruct.ValidationNotAnyOfError(self.radio, self._io, u"/types/cw/seq/4")
            self.lengthcheck = (self._io.read_bytes_full()).decode(u"utf-8")

        @property
        def necessary_for_lengthcheck(self):
            if hasattr(self, '_m_necessary_for_lengthcheck'):
                return self._m_necessary_for_lengthcheck

            if len(self.lengthcheck) != 0:
                self._m_necessary_for_lengthcheck = int(self.lengthcheck) // 0

            return getattr(self, '_m_necessary_for_lengthcheck', None)

        @property
        def cw_beacon(self):
            if hasattr(self, '_m_cw_beacon'):
                return self._m_cw_beacon

            self._m_cw_beacon = self.power + self.avionics + self.payload + self.radio
            return getattr(self, '_m_cw_beacon', None)


    class Ssdv(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.ax25_frame = Silversat.Ssdv.Ax25Frame(self._io, self, self._root)

        class Ax25Frame(KaitaiStruct):
            def __init__(self, _io, _parent=None, _root=None):
                self._io = _io
                self._parent = _parent
                self._root = _root if _root else self
                self._read()

            def _read(self):
                self.ax25_header = Silversat.Ssdv.Ax25Header(self._io, self, self._root)
                self.ax25_info = Silversat.Ssdv.SsdvPayload(self._io, self, self._root)


        class Ax25Header(KaitaiStruct):
            def __init__(self, _io, _parent=None, _root=None):
                self._io = _io
                self._parent = _parent
                self._root = _root if _root else self
                self._read()

            def _read(self):
                self.dest_callsign_raw = Silversat.Ssdv.CallsignRaw(self._io, self, self._root)
                self.dest_ssid_raw = Silversat.Ssdv.SsidMask(self._io, self, self._root)
                self.src_callsign_raw = Silversat.Ssdv.CallsignRaw(self._io, self, self._root)
                self.src_ssid_raw = Silversat.Ssdv.SsidMask(self._io, self, self._root)
                self.ctl = self._io.read_u1()
                self.pid = self._io.read_u1()


        class Callsign(KaitaiStruct):
            def __init__(self, _io, _parent=None, _root=None):
                self._io = _io
                self._parent = _parent
                self._root = _root if _root else self
                self._read()

            def _read(self):
                self.callsign = (self._io.read_bytes(6)).decode(u"ASCII")


        class SsdvPayload(KaitaiStruct):
            def __init__(self, _io, _parent=None, _root=None):
                self._io = _io
                self._parent = _parent
                self._root = _root if _root else self
                self._read()

            def _read(self):
                self.ssdv_sync_byte = self._io.read_u1()
                if not self.ssdv_sync_byte == 85:
                    raise kaitaistruct.ValidationNotEqualError(85, self.ssdv_sync_byte, self._io, u"/types/ssdv/types/ssdv_payload/seq/0")
                self.ssdv_packet_type = self._io.read_u1()
                if not  ((self.ssdv_packet_type == 102) or (self.ssdv_packet_type == 103)) :
                    raise kaitaistruct.ValidationNotAnyOfError(self.ssdv_packet_type, self._io, u"/types/ssdv/types/ssdv_payload/seq/1")
                self.ssdv_callsign = self._io.read_u4be()
                if not self.ssdv_callsign == 3739973996:
                    raise kaitaistruct.ValidationNotEqualError(3739973996, self.ssdv_callsign, self._io, u"/types/ssdv/types/ssdv_payload/seq/2")
                self.ssdv_image_id = self._io.read_u1()
                self.ssdv_packet_id = self._io.read_u2be()
                self.ssdv_width = self._io.read_u1()
                self.ssdv_height = self._io.read_u1()
                self.ssdv_flags = self._io.read_u1()
                self.ssdv_mcu_offset = self._io.read_u1()
                self.ssdv_mcu_index = self._io.read_u2be()
                self.ssdv_image = []
                i = 0
                while not self._io.is_eof():
                    self.ssdv_image.append(self._io.read_u1())
                    i += 1



        class SsidMask(KaitaiStruct):
            def __init__(self, _io, _parent=None, _root=None):
                self._io = _io
                self._parent = _parent
                self._root = _root if _root else self
                self._read()

            def _read(self):
                self.ssid_mask = self._io.read_u1()

            @property
            def ssid(self):
                if hasattr(self, '_m_ssid'):
                    return self._m_ssid

                self._m_ssid = ((self.ssid_mask & 31) >> 1)
                return getattr(self, '_m_ssid', None)

            @property
            def hbit(self):
                if hasattr(self, '_m_hbit'):
                    return self._m_hbit

                self._m_hbit = ((self.ssid_mask & 128) >> 7)
                return getattr(self, '_m_hbit', None)


        class CallsignRaw(KaitaiStruct):
            def __init__(self, _io, _parent=None, _root=None):
                self._io = _io
                self._parent = _parent
                self._root = _root if _root else self
                self._read()

            def _read(self):
                self._raw__raw_callsign_ror = self._io.read_bytes(6)
                self._raw_callsign_ror = KaitaiStream.process_rotate_left(self._raw__raw_callsign_ror, 8 - (1), 1)
                _io__raw_callsign_ror = KaitaiStream(BytesIO(self._raw_callsign_ror))
                self.callsign_ror = Silversat.Ssdv.Callsign(_io__raw_callsign_ror, self, self._root)




