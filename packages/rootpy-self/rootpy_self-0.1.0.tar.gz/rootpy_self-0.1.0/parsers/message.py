from ..proto import ProtobufReader, parse_id, deep_extract_text


class MessageParser:
    @staticmethod
    def parse_list(data):
        messages = []
        if len(data) <= 5:
            return messages
        
        try:
            reader = ProtobufReader(data[5:])
            while not reader.is_eof():
                tag = reader.read_varint()
                field, wire = tag >> 3, tag & 7
                
                if wire == 2:
                    length = reader.read_varint()
                    field_data = reader.read_bytes(length)
                    
                    if field == 5:
                        inner_msgs = MessageParser.parse_inner_list(field_data)
                        messages.extend(inner_msgs)
                elif wire == 0:
                    reader.read_varint()
                elif wire == 1:
                    reader.read_bytes(8)
                elif wire == 5:
                    reader.read_bytes(4)
        except:
            pass
        return messages

    @staticmethod
    def parse_inner_list(data):
        messages = []
        try:
            reader = ProtobufReader(data)
            while not reader.is_eof():
                tag = reader.read_varint()
                field, wire = tag >> 3, tag & 7
                
                if wire == 2:
                    length = reader.read_varint()
                    field_data = reader.read_bytes(length)
                    
                    if field == 11:
                        msg_data = MessageParser.parse_message(field_data)
                        if msg_data and msg_data.get("content"):
                            messages.append(msg_data)
                elif wire == 0:
                    reader.read_varint()
                elif wire == 1:
                    reader.read_bytes(8)
                elif wire == 5:
                    reader.read_bytes(4)
        except:
            pass
        return messages

    @staticmethod
    def parse_message(data):
        try:
            reader = ProtobufReader(data)
            result = {}
            
            while not reader.is_eof():
                tag = reader.read_varint()
                field, wire = tag >> 3, tag & 7
                
                if wire == 0:
                    reader.read_varint()
                elif wire == 1:
                    reader.read_bytes(8)
                elif wire == 2:
                    length = reader.read_varint()
                    field_data = reader.read_bytes(length)
                    
                    if field == 3:
                        ids = parse_id(field_data)
                        if ids["p1"]:
                            result["community_id"] = (ids["p1"], ids["p2"])
                    elif field == 4:
                        ids = parse_id(field_data)
                        if ids["p1"]:
                            result["channel_id"] = (ids["p1"], ids["p2"])
                    elif field == 5:
                        ids = parse_id(field_data)
                        if ids["p1"]:
                            result["author_id"] = (ids["p1"], ids["p2"])
                    elif field == 6:
                        ids = parse_id(field_data)
                        if ids["p1"]:
                            result["message_id"] = (ids["p1"], ids["p2"])
                    elif field == 10:
                        try:
                            text = field_data.decode("utf-8", errors="replace")
                            if text:
                                result["content"] = text
                        except:
                            pass
                    elif field == 13:
                        try:
                            text = field_data.decode("utf-8", errors="strict")
                            if text.startswith("root://emoji/"):
                                emoji = text.replace("root://emoji/", "")
                                if not result.get("content"):
                                    result["content"] = f"[{emoji}]"
                        except:
                            pass
                elif wire == 5:
                    reader.read_bytes(4)
            
            return result if result.get("content") else None
        except:
            return None

    @staticmethod
    def parse_ws_message(data):
        try:
            reader = ProtobufReader(data)
            result = {"content": None}

            while not reader.is_eof():
                tag = reader.read_varint()
                field, wire = tag >> 3, tag & 7

                if wire == 0:
                    reader.read_varint()
                elif wire == 2:
                    length = reader.read_varint()
                    field_data = reader.read_bytes(length)

                    if field == 3:
                        event = MessageParser.parse_event_container(field_data)
                        if event:
                            result.update(event)
                else:
                    reader.skip_field(wire)

            return result if result.get("content") else None
        except:
            return None

    @staticmethod
    def parse_event_container(data):
        try:
            reader = ProtobufReader(data)
            result = {}

            while not reader.is_eof():
                tag = reader.read_varint()
                field, wire = tag >> 3, tag & 7

                if wire == 0:
                    reader.read_varint()
                elif wire == 2:
                    length = reader.read_varint()
                    field_data = reader.read_bytes(length)

                    if field >= 100:
                        msg = MessageParser.parse_event(field_data)
                        if msg and msg.get("content"):
                            result.update(msg)
                    elif field == 3:
                        ids = parse_id(field_data)
                        if ids["p1"]:
                            result["community_id"] = (ids["p1"], ids["p2"])
                    elif field == 4:
                        ids = parse_id(field_data)
                        if ids["p1"]:
                            result["channel_id"] = (ids["p1"], ids["p2"])
                else:
                    reader.skip_field(wire)

            return result
        except:
            return None

    @staticmethod
    def parse_event(data):
        try:
            reader = ProtobufReader(data)
            result = {}
            all_texts = []

            while not reader.is_eof():
                tag = reader.read_varint()
                field, wire = tag >> 3, tag & 7

                if wire == 0:
                    reader.read_varint()
                elif wire == 1:
                    reader.read_bytes(8)
                elif wire == 2:
                    length = reader.read_varint()
                    field_data = reader.read_bytes(length)

                    if field == 3:
                        ids = parse_id(field_data)
                        if ids["p1"]:
                            result["community_id"] = (ids["p1"], ids["p2"])
                    elif field == 4:
                        ids = parse_id(field_data)
                        if ids["p1"]:
                            result["channel_id"] = (ids["p1"], ids["p2"])
                    elif field == 5:
                        ids = parse_id(field_data)
                        if ids["p1"]:
                            result["author_id"] = (ids["p1"], ids["p2"])
                    elif field == 6:
                        ids = parse_id(field_data)
                        if ids["p1"]:
                            result["message_id"] = (ids["p1"], ids["p2"])
                    elif field == 10:
                        text = deep_extract_text(field_data)
                        if text:
                            all_texts.append((field, text))
                    else:
                        text = deep_extract_text(field_data)
                        if text and len(text) >= 1:
                            all_texts.append((field, text))
                elif wire == 5:
                    reader.read_bytes(4)
                else:
                    reader.skip_field(wire)

            if all_texts:
                for f, t in all_texts:
                    if f == 10:
                        result["content"] = t
                        break
                if not result.get("content"):
                    all_texts.sort(key=lambda x: len(x[1]), reverse=True)
                    result["content"] = all_texts[0][1]

            return result if result.get("content") else None
        except:
            return None
