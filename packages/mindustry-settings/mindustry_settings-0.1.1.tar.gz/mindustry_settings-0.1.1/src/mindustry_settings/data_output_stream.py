# Based on data_input_stream.py
import struct
from io import BufferedWriter


class DataOutputStream:
    def __init__(self, stream: BufferedWriter):
        self.stream = stream

    def write_boolean(self, value: bool):
        self.stream.write(struct.pack('?', bytes(value)))

    def write_byte(self, value: int):
        self.stream.write(struct.pack('b', value))

    def write_bytes(self, values: list[int]):
        for value in values:
            self.stream.write(struct.pack('b', bytes(value)))

    def write_unsigned_byte(self, value: int):
        if value < 0: raise ValueError("Expected non-negative, received negative.")
        self.stream.write(struct.pack('B', value))

    def write_char(self, value: str):
        if len(str) > 1: raise ValueError("Expected string of length one or less.")
        self.stream.write(struct.pack('>H', value.encode()))

    def write_double(self, value: float):
        self.stream.write(struct.pack('>d', value))

    def write_float(self, value: float):
        self.stream.write(struct.pack('>f', value))

    def write_short(self, value: int):
        self.stream.write(struct.pack('>h', value))

    def write_unsigned_short(self, value: int):
        if value < 0: raise ValueError("Expected non-negative, received negative.")
        self.stream.write(struct.pack('>H', value))

    def write_long(self, value: int):
        self.stream.write(struct.pack('>q', value))

    def write_utf(self, value: bytes):
        self.stream.write(struct.pack('>H', len(value)))
        self.stream.write(value)
        # utf_length = struct.unpack('>H', self.stream.read(2))[0]
        # return self.stream.read(utf_length)

    def write_str(self, value: str):
        self.write_utf(value.encode())
        # utf = self.read_utf()
        # return utf.decode(errors="ignore")

    def write_int(self, value: int):
        self.stream.write(struct.pack('>i', value))
