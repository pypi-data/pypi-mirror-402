# based on:
# https://github.com/Anuken/Arc/blob/514b290fde467e5875e01151dc48a66a96d31ac5/arc-core/src/arc/Settings.java#L159-L207
# relevant license terms for above source code applies here
import os.path
from enum import Enum
from io import BufferedRandom
from typing import Any
from pathlib import Path

from src.mindustry_settings.data_input_stream import DataInputStream
from src.mindustry_settings.data_output_stream import DataOutputStream


class _ValueType(Enum):
    # protected final static byte typeBool = 0, typeInt = 1, typeLong = 2, typeFloat = 3, typeString = 4, typeBinary = 5
    bool_ = 0
    int_ = 1
    long_ = 2
    float_ = 3
    string_ = 4
    binary_ = 5


class MindustrySettings:
    _settings: dict[str, Any]
    __file: BufferedRandom
    __stream: DataInputStream
    __modified: bool

    def __init__(self, path: Path):
        self._settings = dict()
        self.__file = path.open("rb+")
        self.__stream = DataInputStream(self.__file)
        self.__modified = False
        self.load(os.path.getsize(path) == 0)

    def load(self, empty: bool = False):
        if empty: return

        self.__file.seek(0)
        amount = self.__stream.read_int()
        # anuke's theory on detecting corruption
        # also keeps behavior consistent
        if amount <= 0: raise IOError("Zero values exist in settings.")

        for i in range(amount):
            key = self.__stream.read_str()
            type_ = self.__stream.read_byte()
            value = self.__read_type(type_)
            
            self._settings[key] = value

    def set_file(self, path: Path):
        self.__file = path.open("rb+")
        self.__stream = DataInputStream(self.__file)
        self.load()

    def get_bool(self, key: str) -> bool:
        value = self._settings.get(key)
        if value is not bool: raise TypeError("Returned value is not a boolean.")
        return value

    def get_int(self, key: str) -> int:
        value = self._settings.get(key)
        if value is not int: raise TypeError("Returned value is not an int.")
        return value

    def get_float(self, key: str) -> float:
        value = self._settings.get(key)
        if value is not float: raise TypeError("Returned value is not a float.")
        return value

    def get_binary(self, key: str) -> list[int]:
        value = self._settings.get(key)
        if value is not list[int]: raise TypeError("Returned value is not binary.")
        return value

    def get_string(self, key: str) -> str:
        value = self._settings.get(key)
        if type(value) != str: raise TypeError(f"Returned value is not a string.")
        return value

    def set_value(self, key: str, value: Any):
        self._settings[key] = value
        self.__modified = True

    def write_to_disk(self):
        # I don't want arthritis at my young age
        self.__file.truncate(0)
        self.__file.seek(0)
        stream = DataOutputStream(self.__file)
        stream.write_int(len(self._settings))

        for key in self._settings:
            value = self._settings[key]
            if not self.type_valid(type(value)): raise ValueError(f"Invalid type. Got type {type(value)}.")
            stream.write_str(key)

            if type(value) == bool:
                stream.write_byte(_ValueType.bool_.value)
                stream.write_boolean(value)
            elif type(value) == int:
                stream.write_byte(_ValueType.int_.value)
                stream.write_int(value)
            elif type(value) == float:
                stream.write_byte(_ValueType.float_.value)
                stream.write_float(value)
            elif type(value) == list[int]:
                stream.write_byte(_ValueType.binary_.value)
                stream.write_int(len(value))
                stream.write_bytes(value)
            elif type(value) == str:
                stream.write_byte(_ValueType.string_.value)
                stream.write_str(value)

        self.__modified = False

    def type_valid(self, type_: type) -> bool:
        allowed_types = [bool, int, float, list[int], str]
        for value in allowed_types:
            if value == type_: return True
        return False

    def __read_type(self, type_: int) -> Any:
        # makes the boilerplate less arthritis inducing
        stream = self.__stream

        if _ValueType.bool_.value == type_:
            return stream.read_boolean()
        elif _ValueType.int_.value == type_:
            return stream.read_int()
        elif _ValueType.long_.value == type_:
            return stream.read_long()
        elif _ValueType.float_.value == type_:
            return stream.read_float()
        elif _ValueType.binary_.value == type_:
            length = stream.read_int()
            return stream.read_bytes(length)
        elif _ValueType.string_.value == type_:
            return stream.read_str()

        raise ValueError(f"Type does not exist for byte {type_}.")

    def __del__(self):
        if self.__modified: self.write_to_disk()
        self.__file.close()
