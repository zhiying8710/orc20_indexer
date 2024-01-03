import base64
from typing import Union


class InscriptionTransactionParseResult:

    def __init__(self, content_type, content):
        self.content_type = content_type
        self.content = content


class InscriptionTransactionParser:
    def __init__(self):
        self.pointer = 0
        self.raw = None

    @staticmethod
    def hex_string_to_byte_array(hex_string):
        length = len(hex_string)
        data = bytearray(length // 2)
        for i in range(0, length, 2):
            data[i // 2] = int(hex_string[i:i+2], 16)
        return bytes(data)

    @staticmethod
    def byte_array_to_utf8_string(byte_array):
        return byte_array.decode('utf-8')

    @staticmethod
    def byte_array_to_single_byte_chars(byte_array):
        return ''.join(chr(b) for b in byte_array)

    def read_bytes(self, length):
        data = self.raw[self.pointer:self.pointer+length]
        self.pointer += length
        return data

    def get_initial_position(self):
        pattern = self.hex_string_to_byte_array("0063036f7264")
        for i in range(len(self.raw) - len(pattern)):
            if all(self.raw[i + j] == pattern[j] for j in range(len(pattern))):
                return i + len(pattern)
        return -1

    def read_pushdata(self):
        data = self.read_bytes(1)
        length = data[0]
        if 1 <= length <= 75:
            return self.read_bytes(length)
        else:
            size = 1 if length == 76 else (2 if length == 77 else 4)
            size_data = self.read_bytes(size)
            data_size = sum(size_data[i] << (8 * i) for i in range(size))
            return self.read_bytes(data_size)

    @staticmethod
    def has_inscription(witness):
        return "0063036f7264" in ''.join(witness)

    def parse_inscription(self, witness) -> Union[InscriptionTransactionParseResult, None]:
        if not witness:
            return None

        hex_string = ''.join(witness)
        self.raw = self.hex_string_to_byte_array(hex_string)
        self.pointer = self.get_initial_position()
        if self.pointer == -1:
            return None

        try:
            inscription_map = {}
            while self.pointer < len(self.raw) and self.raw[self.pointer] != 0:
                content_type = self.byte_array_to_utf8_string(self.read_pushdata())
                content = self.read_pushdata()
                inscription_map[content_type] = content

            if self.pointer < len(self.raw) and self.raw[self.pointer] == 0:
                self.pointer += 1

            content_list = []
            while self.pointer < len(self.raw) and self.raw[self.pointer] != 104:
                content_list.append(self.read_pushdata())

            total_length = sum(len(content) for content in content_list)
            content_data = bytearray(total_length)
            offset = 0
            for content in content_list:
                content_data[offset:offset+len(content)] = content
                offset += len(content)

            content_type = self.byte_array_to_utf8_string(inscription_map["\u0001"])
            return InscriptionTransactionParseResult(content_type, base64.b64encode(content_data).decode('utf-8'))
        except Exception as e:
            return None


