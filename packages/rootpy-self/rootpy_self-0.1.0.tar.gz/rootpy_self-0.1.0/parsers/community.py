from ..proto import ProtobufReader, parse_id


class CommunityParser:
    @staticmethod
    def parse_list_mine(data):
        communities = []
        if len(data) <= 5:
            return communities
        
        try:
            reader = ProtobufReader(data[5:])
            while not reader.is_eof():
                tag = reader.read_varint()
                field, wire = tag >> 3, tag & 7
                
                if field == 0:
                    break
                
                if wire == 2:
                    length = reader.read_varint()
                    field_data = reader.read_bytes(length)
                    
                    if field == 10:
                        comm = CommunityParser.parse_wrapper(field_data)
                        if comm and comm.get("id"):
                            communities.append(comm)
                elif wire == 0:
                    reader.read_varint()
                elif wire == 1:
                    reader.read_bytes(8)
                elif wire == 5:
                    reader.read_bytes(4)
        except:
            pass
        return communities
    
    @staticmethod
    def parse_wrapper(data):
        try:
            reader = ProtobufReader(data)
            while not reader.is_eof():
                tag = reader.read_varint()
                field, wire = tag >> 3, tag & 7
                
                if field == 0:
                    break
                
                if wire == 2:
                    length = reader.read_varint()
                    field_data = reader.read_bytes(length)
                    
                    if field == 10:
                        return CommunityParser.parse_object(field_data)
                elif wire == 0:
                    reader.read_varint()
                elif wire == 1:
                    reader.read_bytes(8)
                elif wire == 5:
                    reader.read_bytes(4)
        except:
            pass
        return None
    
    @staticmethod
    def parse_object(data):
        try:
            reader = ProtobufReader(data)
            result = {}
            
            while not reader.is_eof():
                tag = reader.read_varint()
                field, wire = tag >> 3, tag & 7
                
                if field == 0:
                    break
                
                if wire == 2:
                    length = reader.read_varint()
                    field_data = reader.read_bytes(length)
                    
                    if field in [3, 4, 10]:
                        ids = parse_id(field_data)
                        if ids["p1"] and not result.get("id"):
                            result["id"] = (ids["p1"], ids["p2"])
                    elif field in [6, 12]:
                        try:
                            name = field_data.decode("utf-8")
                            if name and len(name) > 0 and not name.startswith("#"):
                                result["name"] = name
                        except:
                            pass
                elif wire == 0:
                    reader.read_varint()
                elif wire == 1:
                    reader.read_bytes(8)
                elif wire == 5:
                    reader.read_bytes(4)
            
            return result if result.get("id") else None
        except:
            return None
