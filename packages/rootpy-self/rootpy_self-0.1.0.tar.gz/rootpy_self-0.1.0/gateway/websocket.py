import threading
import time
import ssl
import websocket

from ..constants import WS_URL, ROOT_VERSION
from ..proto import create_id_message, encode_varint
from ..parsers import MessageParser
from ..models import Message


class WebSocketGateway:
    def __init__(self, client, token, device_id, device_id_parts):
        self.client = client
        self.token = token
        self.device_id = device_id
        self.device_id_part1, self.device_id_part2 = device_id_parts
        self.ws = None
        self.running = False
        self._seen = set()

    def connect(self):
        self.running = True
        headers = [
            f"User-Agent: {ROOT_VERSION}",
            f"x-root-Device-Id: {self.device_id}",
            f"Authorization: Bearer {self.token}",
        ]

        self.ws = websocket.WebSocketApp(
            WS_URL,
            header=headers,
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close,
            on_open=self._on_open,
        )

        t = threading.Thread(
            target=lambda: self.ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE}),
            daemon=True,
        )
        t.start()

    def close(self):
        self.running = False
        if self.ws:
            self.ws.close()

    def _on_message(self, ws, message):
        try:
            if isinstance(message, bytes):
                if b'\xd2\x0a' in message or b'\xf2\x0a' in message:
                    parsed = MessageParser.parse_ws_message(message)
                    if parsed and parsed.get("content"):
                        msg = Message(parsed, self.client)
                        key = hash(msg.content[:50] if len(msg.content) > 50 else msg.content)
                        if key not in self._seen:
                            self._seen.add(key)
                            self.client.on_message(msg)
        except:
            pass

    def _on_error(self, ws, error):
        pass

    def _on_close(self, ws, status, msg):
        if self.running:
            time.sleep(5)
            self.connect()

    def _on_open(self, ws):
        print("[OK] WebSocket connected (DMs)")
        try:
            sub_msg = b""
            device_payload = create_id_message(self.device_id_part1, self.device_id_part2)
            sub_msg += bytes([0x52]) + encode_varint(len(device_payload)) + device_payload
            ws.send(sub_msg, opcode=websocket.ABNF.OPCODE_BINARY)
        except:
            pass
