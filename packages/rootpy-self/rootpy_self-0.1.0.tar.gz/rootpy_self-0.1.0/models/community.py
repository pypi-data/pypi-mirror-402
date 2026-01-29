class Community:
    def __init__(self, data):
        self.id = data.get("id")
        self.name = data.get("name", "Unknown")
        self.channels = []
    
    def __repr__(self):
        return f"<Community name='{self.name}'>"
