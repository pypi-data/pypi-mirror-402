from ..proto import ProtobufReader, parse_id


class ChannelParser:
    @staticmethod
    def parse_groups(data):
        groups = []
        if len(data) <= 5:
            return groups
        
        try:
            reader = ProtobufReader(data[5:])
            while not reader.is_eof():
                tag = reader.read_varint()
                field, wire = tag >> 3, tag & 7
                
                if wire == 2:
                    length = reader.read_varint()
                    field_data = reader.read_bytes(length)
                    
                    if field == 10:
                        group = ChannelParser.parse_group(field_data)
                        if group:
                            groups.append(group)
                elif wire == 0:
                    reader.read_varint()
                elif wire == 1:
                    reader.read_bytes(8)
                elif wire == 5:
                    reader.read_bytes(4)
        except:
            pass
        return groups

    @staticmethod
    def parse_group(data):
        try:
            reader = ProtobufReader(data)
            result = {}
            
            while not reader.is_eof():
                tag = reader.read_varint()
                field, wire = tag >> 3, tag & 7
                
                if wire == 2:
                    length = reader.read_varint()
                    field_data = reader.read_bytes(length)
                    
                    if field == 10:
                        ids = parse_id(field_data)
                        if ids["p1"]:
                            result["community_id"] = (ids["p1"], ids["p2"])
                    elif field == 11:
                        ids = parse_id(field_data)
                        if ids["p1"]:
                            result["id"] = (ids["p1"], ids["p2"])
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
            
            return result if result.get("id") else None
        except:
            return None

    @staticmethod
    def parse_list(data):
        channels = []
        if len(data) <= 5:
            return channels
        
        try:
            reader = ProtobufReader(data[5:])
            while not reader.is_eof():
                tag = reader.read_varint()
                field, wire = tag >> 3, tag & 7
                
                if wire == 2:
                    length = reader.read_varint()
                    field_data = reader.read_bytes(length)
                    
                    if field == 10:
                        channel = ChannelParser.parse_channel(field_data)
                        if channel:
                            channels.append(channel)
                elif wire == 0:
                    reader.read_varint()
                elif wire == 1:
                    reader.read_bytes(8)
                elif wire == 5:
                    reader.read_bytes(4)
        except:
            pass
        return channels

    @staticmethod
    def parse_channel(data):
        try:
            reader = ProtobufReader(data)
            result = {}
            
            while not reader.is_eof():
                tag = reader.read_varint()
                field, wire = tag >> 3, tag & 7
                
                if wire == 2:
                    length = reader.read_varint()
                    field_data = reader.read_bytes(length)
                    
                    if field == 10:
                        ids = parse_id(field_data)
                        if ids["p1"]:
                            result["community_id"] = (ids["p1"], ids["p2"])
                    elif field == 11:
                        ids = parse_id(field_data)
                        if ids["p1"]:
                            result["channel_group_id"] = (ids["p1"], ids["p2"])
                    elif field == 12:
                        ids = parse_id(field_data)
                        if ids["p1"]:
                            result["id"] = (ids["p1"], ids["p2"])
                    elif field == 13:
                        try:
                            result["name"] = field_data.decode("utf-8")
                        except:
                            pass
                    elif field == 14:
                        try:
                            result["description"] = field_data.decode("utf-8")
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
