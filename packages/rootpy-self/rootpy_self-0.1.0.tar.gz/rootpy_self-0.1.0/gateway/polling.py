import threading
import time

from ..models import Message


class PollingGateway:
    def __init__(self, client):
        self.client = client
        self.running = False
        self._poll_interval = 0.1
        self._seen = set()
        self._first_run = True

    def start(self, poll_interval=0.1):
        self._poll_interval = poll_interval
        self.running = True
        self._first_run = True
        
        thread = threading.Thread(target=self._poll_loop, daemon=True)
        thread.start()

    def stop(self):
        self.running = False

    def _poll_loop(self):
        while self.running:
            for (ch_id, comm_id), state in list(self.client._monitored_channels.items()):
                try:
                    messages = self.client.list_messages(ch_id, comm_id, limit=3)
                    
                    if self._first_run:
                        for msg_data in messages:
                            msg_id = msg_data.get("message_id")
                            content = msg_data.get("content", "")
                            if msg_id:
                                self._seen.add(f"{msg_id[0]}:{msg_id[1]}")
                            if content:
                                self._seen.add(f"content:{hash(content)}")
                            author_id = msg_data.get("author_id")
                            if author_id and comm_id:
                                threading.Thread(
                                    target=self.client._prefetch_user,
                                    args=(author_id, comm_id),
                                    daemon=True
                                ).start()
                        continue
                    
                    for msg_data in reversed(messages):
                        msg_id = msg_data.get("message_id")
                        content = msg_data.get("content", "")
                        
                        is_seen = False
                        if msg_id:
                            msg_key = f"{msg_id[0]}:{msg_id[1]}"
                            if msg_key in self._seen:
                                is_seen = True
                            else:
                                self._seen.add(msg_key)
                        
                        if content:
                            content_key = f"content:{hash(content)}"
                            if content_key in self._seen:
                                is_seen = True
                            else:
                                self._seen.add(content_key)
                        
                        if not is_seen and content:
                            msg = Message(msg_data, self.client)
                            self.client.on_message(msg)
                except:
                    pass
            
            if self._first_run:
                self._first_run = False
                print("[OK] Loaded existing messages, now listening for new ones...")
            
            time.sleep(self._poll_interval)
