#messages.py
import ctypes
from enum import Enum
from crcccitt import *

class IllegalMessage(Exception):
    pass

class FrameControl(Enum):
    BeaconOrBroadcast = 0x22
    Directed = 0x20
    ShortBroadcast = 0x04
    ShortDirected = 0x05

class MessageBase:
    NumPreambleBits = 48
    NumSyncWordBits = 16
    NumPreambleAndSyncBits = NumPreambleBits + NumSyncWordBits
    NumLengthBits = 8

    PreambleBits = NumPreambleBits + NumSyncWordBits + NumLengthBits

    NumCrcBits = 32
    PostableBits = NumCrcBits

    MessagePacketOverhead = PreambleBits + PostableBits


    def __init__(self, msg=None, msglength=None, srcuid=None, dstuid=None, crcvalid=True):
        assert (msglength is not None)
        # assert (isinstance(msgtype, MessageTypes))
        # if (messagetype != MessageTypes.ShortDirected):
        #     assert (srcuid is not None)
        # elif ((messagetype == MessageTypes.Directed) or (messagetype == MessageTypes.ShortDirected)):
        #     assert (dstuid is not None)

        if msglength is not None:
            self.msglength = msglength * 8 + MessageBase.MessagePacketOverhead

        self.srcuid = srcuid
        self.dstuid = dstuid
        self.crcvalid = crcvalid
        self.msg = msg

    @property
    def Buffer(self) -> bytes:
        return self.data

    @Buffer.setter
    def Buffer(self, value: bytes):
        self.data = value

    class MsgCRC(ctypes.BigEndianStructure):
        _pack_ = 1  # force byte alignment
        _fields_ = [("crc16", ctypes.c_uint16)] # added by radio

    @property
    def msgcrc(self):
        msgcrc = self.MsgCRC.from_buffer(self.data[-2:])
        return msgcrc.crc16

    @property
    def crc16(self):
        return CRCCCITT.CalculateCrc16(self.data[:-2], 0xffff)

    @property
    def CRCValid(self):
        return self.crcvalid

    @CRCValid.setter
    def CRCValid(self, value: bool):
        assert (isinstance(value, bool))
        self.crcvalid = value

    @property
    def TotalPacketBits(self):
        return self.msglength

    def __len__(self):
        return len(self.Buffer)

    def __str__(self):
        return f"{type(self).__name__: <28}: {self.Buffer.hex()}"



class BeaconMessagePacket(MessageBase, ctypes.BigEndianStructure):
    _pack_ = 1  # force byte alignment
    _fields_ = [
        # ("length", ctypes.c_uint8),  # added by radio
        ("eirp", ctypes.c_uint8),
        ("subnet", ctypes.c_uint8),
        ("framecontrol", ctypes.c_uint8),
        ("msgid", ctypes.c_uint8),
        ("addrctrl", ctypes.c_uint8),
        ("srcuid", ctypes.c_uint64),
        # ("crc16", ctypes.c_uint16) # added by radio
    ]


class BroadcastMessagePacket(MessageBase, ctypes.BigEndianStructure):
    _pack_ = 1  # force byte alignment
    _fields_ = [
        ("length", ctypes.c_uint8),  # added by radio
        ("eirp", ctypes.c_uint8),
        ("subnet", ctypes.c_uint8),
        ("framecontrol", ctypes.c_uint8),
        ("msgid", ctypes.c_uint8),
        ("addrctrl", ctypes.c_uint8),
        ("srcuid", ctypes.c_uint64),
        ("opentag", ctypes.c_uint8 * 8),
        # ("crc16", ctypes.c_uint16) # added by radio
    ]

class DirectedMessagePacket(MessageBase, ctypes.BigEndianStructure):
    _pack_ = 1  # force byte alignment
    _fields_ = [
        ("length", ctypes.c_uint8),  # added by radio
        ("eirp", ctypes.c_uint8),
        ("subnet", ctypes.c_uint8),
        ("framecontrol", ctypes.c_uint8),
        ("msgid", ctypes.c_uint8),
        ("addrctrl", ctypes.c_uint8),
        ("srcuid", ctypes.c_uint64),
        ("dstuid", ctypes.c_uint64),
        ("opentag", ctypes.c_uint8),
        # ("crc16", ctypes.c_uint16) # added by radio
    ]


class ShortBroadcastMessagePacket(MessageBase, ctypes.BigEndianStructure):
    _pack_ = 1  # force byte alignment
    _fields_ = [
        ("length", ctypes.c_uint8),  # added by radio
        ("eirp", ctypes.c_uint8),
        ("msgid", ctypes.c_uint8),
        ("framecontrol", ctypes.c_uint8),
        ("srcuid", ctypes.c_uint64),
        # ("crc16", ctypes.c_uint16) # added by radio
    ]

    def __init__(self,
                 eirp=None,
                 msgid=None,
                 framecontrol=FrameControl.ShortBroadcast,
                 srcuid=None,
                 data=None
                 ):
        assert (eirp is not None), "eirp must be set"
        assert (msgid is not None), "msgid must be set"
        assert (srcuid is not None), "srcuid must be set"

        self.eirp = eirp
        self.msgid = msgid
        self.framecontrol = framecontrol.value
        # self.srcuid = srcuid

        self.data = data
        msglength=len(self)
        super().__init__(msg=self, msglength=msglength, srcuid=srcuid)


class UnknownMessagePacket(MessageBase, ctypes.BigEndianStructure):
    _pack_ = 1  # force byte alignment
    _fields_ = [
        ("length", ctypes.c_uint8),  # added by radio
        ("eirp", ctypes.c_uint8),
    ]

    def __init__(self,
                 eirp=None,
                 data=None
                 ):
        assert (eirp is not None), "eirp must be set"

        self.eirp = eirp
        self.msgid = msgid
        self.framecontrol = framecontrol.value
        # self.srcuid = srcuid

        self.data = data
        assert False, "not done yet"
        self.length = len(self)
        super().__init__(msg=self, msglength=msglength)


class ShortDirectedMessagePacket(ctypes.BigEndianStructure, MessageBase):
    _pack_ = 1  # force byte alignment
    _fields_ = [
        ("length", ctypes.c_uint8),  # added by radio
        ("eirp", ctypes.c_uint8),
        ("msgid", ctypes.c_uint8),
        ("framecontrol", ctypes.c_uint8),
        ("dstuid", ctypes.c_uint64),
        # ("crc16", ctypes.c_uint16) # added by radio
    ]


class MessageFactory(ctypes.Structure):
    _pack_ = 1  # force byte alignment
    _fields_ = [
        # All but Short Broadcast have this structure
        ("length", ctypes.c_uint8),
        ("eirp", ctypes.c_uint8),
        ("subnet", ctypes.c_uint8),
        ("framecontrol", ctypes.c_uint8),
        ("msgid", ctypes.c_uint8),
        ("addrctrl", ctypes.c_uint8),
    ]

    @staticmethod
    def CreateMessage(offset:int, msgbuf: bytes):
        # skip over length
        # print(cmdclass, offset, hexstringbuffer)
        msgbufba = bytearray(msgbuf)
        instance = MessageFactory.from_buffer(msgbufba[offset:offset+ctypes.sizeof(MessageFactory)])
        return instance.createmessage(offset, msgbufba)

    def createmessage(self, offset:int, msgbufba: bytearray):
        newoffset = None
        length = msgbufba[0]
        # check for the most common one first
        framecontrol = self.framecontrol
        if framecontrol == 0x04:
            # Short Broadcast Message
            assert length >= ctypes.sizeof(ShortBroadcastMessagePacket)
            instance = ShortBroadcastMessagePacket.from_buffer(msgbufba[offset:])
            instance.Buffer = msgbufba[offset:offset + length]
            newoffset = offset + length
        # check for next likely message
        elif framecontrol == 0x20:
            # Directed Message
            assert length >= ctypes.sizeof(DirectedMessagePacket)
            instance = DirectedMessagePacket.from_buffer(msgbufba[offset:offset + length])
            instance.Buffer = msgbufba[offset:offset + length]
            newoffset = offset + length
        elif framecontrol == 0x05:
            # Short Directed Message
            assert length >= ctypes.sizeof(ShortDirectedMessagePacket)
            instance = ShortDirectedMessagePacket.from_buffer(msgbufba[offset:offset + length])
            instance.Buffer = msgbufba[offset:offset + length]
            newoffset = offset + length
        elif framecontrol == 0x22:
            # either Beacon or Broadcast
            addrctrl = self.addrctrl
            if addrctrl == 0x40:
                # Create Beacon Message
                assert length >= ctypes.sizeof(BeaconMessagePacket)
                instance = BeaconMessagePacket.from_buffer(msgbufba[offset:offset + length])
                instance.Buffer = msgbufba[offset:offset + length]
                newoffset = offset + length
            elif addrctrl == 0x41:
                # Create Broadcast Message
                assert length >= ctypes.sizeof(BroadcastMessagePacket)
                instance = BroadcastMessagePacket.from_buffer(msgbufba[offset:offset + length])
                instance.Buffer = msgbufba[offset:offset + length]
                newoffset = offset + length
            else:
                raise IllegalMessage(f"Bad Address Control Field(0x{addrctrl:02X})")
        else:
            assert length >= ctypes.sizeof(UnknownMessagePacket)
            instance = UnknownMessagePacket.from_buffer(msgbufba[offset:offset + length])
            instance.Buffer = msgbufba[offset:offset + length]
            if length == 36:
                foo = msgbufba[offset:offset + length].hex()
                bar = 3
            newoffset = offset + length
        return newoffset, instance

## Messages have length
## messages have a valid or invalid CRC
## message have a time of flight duration


# class Message:
#
#
#     # BeaconMessagePacketOverhead = ( \
#     #             8 +  # EIRP
#     #             8 +  # subnet 0xFF
#     #             8 +  # frame control
#     #             8 +  # message ID
#     #             8 +  # address control
#     #             64  # source uid
#     # )
#     #
#     # BroadcastMessagePacketOverhead = ( \
#     #             8 +  # EIRP
#     #             8 +  # subnet 0xFF
#     #             8 +  # frame control
#     #             8 +  # message ID
#     #             8 +  # address control
#     #             64 +  # source uid
#     #             4 * 8 # open tag overhead
#     # )
#     #
#     # DirectedMessagePacketOverhead = ( \
#     #             8 +  # EIRP
#     #             8 +  # subnet 0xFF
#     #             8 +  # frame control
#     #             8 +  # message ID
#     #             8 +  # address control
#     #             64 +  # source uid
#     #             64 +  # destination UID
#     #             8  # open tag overhead
#     # )
#     #
#     # ShortBroadcastMessagePacketOverhead = ( \
#     #             8 +  # EIRP
#     #             8 +  # MsgID
#     #             8 +  # frame control
#     #             64  # source uid
#     # )
#     #
#     # ShortDirectedMessagePacketOverhead = ( \
#     #             8 +  # EIRP
#     #             8 +  # MsgID
#     #             8 +  # frame control
#     #             64  # destination UID
#     # )
#
#     overheaddict = {
#         MessageTypes.BeaconOrBroadcast: ctypes.sizeof(BeaconMessagePacket) * 8,
#         MessageTypes.Directed : ctypes.sizeof(DirectedMessagePacket) * 8,
#         MessageTypes.ShortBroadcast : ctypes.sizeof(ShortBroadcastMessagePacket) * 8,
#         MessageTypes.ShortDirected : ctypes.sizeof(ShortDirectedMessagePacket) * 8
#     }
#
#     def __init__(self, msg=None, messagetype: MessageTypes = None, msglength=None, srcuid=None, dstuid=None, crcvalid=True):
#         assert (msglength is not None)
#         assert (isinstance(msgtype, MessageTypes))
#         if (messagetype != MessageTypes.ShortDirected):
#             assert (srcuid is not None)
#         elif ((messagetype == MessageTypes.Directed) or (messagetype == MessageTypes.ShortDirected)):
#             assert (dstuid is not None)
#
#         if msglength is not None:
#             self.msglength = msglength * 8 + overheaddict[messagetype]
#         else:
#             if len(msg):
#                 self.msglen = len(msg) * 8
#             else:
#                 self.msglen = msglength
#         self.srcuid = srcuid
#         self.dstuid = dstuid
#         self.crcvalid = crcvalid
#         self.msg = msg
#
#     @property
#     def CRCValid(self):
#         return self.crcvalid
#
#     @CRCValid.setter
#     def CRCValid(self, value: bool):
#         assert (isinstance(value, bool))
#         self.crcvalid = value
