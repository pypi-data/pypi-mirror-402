from ..proto import ProtobufReader, parse_id


class UserParser:
    @staticmethod
    def parse_response(data):
        if len(data) <= 5:
            return None
        
        try:
            reader = ProtobufReader(data[5:])
            result = {}
            
            while not reader.is_eof():
                tag = reader.read_varint()
                field, wire = tag >> 3, tag & 7
                
                if field == 0:
                    break
                
                if wire == 2:
                    length = reader.read_varint()
                    field_data = reader.read_bytes(length)
                    
                    if field == 10:
                        ids = parse_id(field_data)
                        if ids["p1"]:
                            result["id"] = (ids["p1"], ids["p2"])
                    elif field == 11:
                        try:
                            inner_reader = ProtobufReader(field_data)
                            while not inner_reader.is_eof():
                                inner_tag = inner_reader.read_varint()
                                inner_field, inner_wire = inner_tag >> 3, inner_tag & 7
                                if inner_wire == 2:
                                    inner_len = inner_reader.read_varint()
                                    inner_data = inner_reader.read_bytes(inner_len)
                                    if inner_field == 1:
                                        result["avatar"] = inner_data.decode("utf-8")
                                        break
                                else:
                                    break
                        except:
                            pass
                    elif field == 12:
                        try:
                            result["name"] = field_data.decode("utf-8")
                        except:
                            pass
                elif wire == 0:
                    reader.read_varint()
                elif wire == 1:
                    reader.read_bytes(8)
                elif wire == 5:
                    reader.read_bytes(4)
            
            return result if result.get("name") else None
        except:
            return None
