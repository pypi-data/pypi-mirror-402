import struct


def encode_varint(value):
    result = []
    while True:
        byte = value & 0x7F
        value >>= 7
        if value == 0:
            result.append(byte)
            break
        result.append(byte | 0x80)
    return bytes(result)


def encode_fixed64(value):
    return struct.pack("<Q", value & 0xFFFFFFFFFFFFFFFF)


def create_id_message(part1, part2):
    payload = b""
    payload += bytes([0x09]) + encode_fixed64(part1)
    payload += bytes([0x11]) + encode_fixed64(part2)
    return payload


def encode_grpc_web_message(data):
    return struct.pack(">BI", 0, len(data)) + data


class ProtobufReader:
    def __init__(self, data):
        self.data = data
        self.pos = 0

    def read_varint(self):
        result = 0
        shift = 0
        while self.pos < len(self.data):
            byte = self.data[self.pos]
            self.pos += 1
            result |= (byte & 0x7F) << shift
            if not (byte & 0x80):
                return result
            shift += 7
        raise Exception("EOF")

    def read_bytes(self, length):
        if self.pos + length > len(self.data):
            raise Exception("EOF")
        data = self.data[self.pos : self.pos + length]
        self.pos += length
        return data

    def read_fixed64(self):
        return struct.unpack("<q", self.read_bytes(8))[0]

    def is_eof(self):
        return self.pos >= len(self.data)

    def skip_field(self, wire_type):
        if wire_type == 0:
            self.read_varint()
        elif wire_type == 1:
            self.read_bytes(8)
        elif wire_type == 2:
            self.read_bytes(self.read_varint())
        elif wire_type == 5:
            self.read_bytes(4)


def parse_id(data):
    reader = ProtobufReader(data)
    ids = {"p1": None, "p2": None}
    while not reader.is_eof():
        try:
            tag = reader.read_varint()
            field, wire = tag >> 3, tag & 7
            if field == 1 and wire == 1:
                ids["p1"] = reader.read_fixed64()
            elif field == 2 and wire == 1:
                ids["p2"] = reader.read_fixed64()
            else:
                reader.skip_field(wire)
        except:
            break
    return ids


def deep_extract_text(data, depth=0):
    if depth > 6:
        return None
    
    try:
        text = data.decode("utf-8", errors="strict")
        printable = sum(c.isalnum() or c.isspace() or c in ".,!?'-:;()[]@#$%&*" for c in text)
        if len(text) > 2 and printable > len(text) * 0.5:
            return text
    except:
        pass
    
    try:
        reader = ProtobufReader(data)
        while not reader.is_eof():
            tag = reader.read_varint()
            field, wire = tag >> 3, tag & 7
            if wire == 2:
                length = reader.read_varint()
                field_data = reader.read_bytes(length)
                result = deep_extract_text(field_data, depth + 1)
                if result and len(result) > 2:
                    return result
            else:
                reader.skip_field(wire)
    except:
        pass
    return None
