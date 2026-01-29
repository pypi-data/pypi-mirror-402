import threading


class Message:
    def __init__(self, data, client, fetch_author=True):
        self._client = client
        self.content = data.get("content", "")
        self.author_id = data.get("author_id")
        self.channel_id = data.get("channel_id")
        self.community_id = data.get("community_id")
        self.message_id = data.get("message_id")
        
        self.channel_name = None
        self.community_name = None
        self.author_name = None
        
        if client and self.channel_id:
            ch_key = self.channel_id
            if ch_key in client._channel_names:
                self.channel_name = client._channel_names[ch_key]
        if client and self.community_id:
            comm_key = self.community_id
            if comm_key in client._community_names:
                self.community_name = client._community_names[comm_key]
        
        if client and self.author_id and self.community_id:
            cache_key = (self.author_id, self.community_id)
            if cache_key in client._user_names:
                self.author_name = client._user_names[cache_key].get("name")
            elif fetch_author:
                threading.Thread(target=self._fetch_author, daemon=True).start()

    def _fetch_author(self):
        try:
            user_info = self._client.get_user(self.author_id, self.community_id)
            if user_info:
                self.author_name = user_info.get("name")
        except:
            pass

    def reply(self, content):
        if self.channel_id:
            return self._client.send_message(self.channel_id, content)
        return False
    
    def __repr__(self):
        return f"<Message content='{self.content[:30]}...'>"
