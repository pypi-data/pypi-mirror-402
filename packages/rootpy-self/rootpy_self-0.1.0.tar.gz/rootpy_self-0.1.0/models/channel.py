class Channel:
    def __init__(self, data):
        self.id = data.get("id")
        self.name = data.get("name", "Unknown")
        self.description = data.get("description", "")
        self.community_id = data.get("community_id")
        self.channel_group_id = data.get("channel_group_id")
        self.group_name = data.get("group_name", "")
    
    def __repr__(self):
        return f"<Channel name='{self.name}'>"
