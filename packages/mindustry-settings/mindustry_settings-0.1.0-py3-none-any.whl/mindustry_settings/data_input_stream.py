# https://stackoverflow.com/a/29526850
# The GPL 3.0 license defined in the root of this repository does NOT apply to the code in this file.
# Rather, the original license for this code, as defined by StackOverFlow, applies instead.
# I.e.: CC BY-SA 3.0

import struct
from io import BufferedRandom


class DataInputStream:
    def __init__(self, stream: BufferedRandom):
        self.stream = stream

    def read_boolean(self) -> bool:
        return struct.unpack('?', self.stream.read(1))[0]

    def read_byte(self) -> int:
        return struct.unpack('b', self.stream.read(1))[0]

    def read_bytes(self, length: int) -> list[int]:
        bytes_ = list()
        for _ in range(length):
            bytes_.append(self.read_byte())

        return bytes_

    def read_unsigned_byte(self) -> int:
        return struct.unpack('B', self.stream.read(1))[0]

    def read_char(self) -> str:
        return chr(struct.unpack('>H', self.stream.read(2))[0])

    def read_double(self) -> float:
        return struct.unpack('>d', self.stream.read(8))[0]

    def read_float(self) -> float:
        return struct.unpack('>f', self.stream.read(4))[0]

    def read_short(self) -> int:
        return struct.unpack('>h', self.stream.read(2))[0]

    def read_unsigned_short(self) -> int:
        return struct.unpack('>H', self.stream.read(2))[0]

    def read_long(self) -> int:
        return struct.unpack('>q', self.stream.read(8))[0]

    def read_utf(self) -> bytes:
        utf_length = struct.unpack('>H', self.stream.read(2))[0]
        return self.stream.read(utf_length)

    def read_str(self) -> str:
        utf = self.read_utf()
        return utf.decode(errors="ignore")

    def read_int(self) -> int:
        return struct.unpack('>i', self.stream.read(4))[0]
