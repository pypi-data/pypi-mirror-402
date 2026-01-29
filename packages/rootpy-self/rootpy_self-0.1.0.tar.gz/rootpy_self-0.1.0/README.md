# rootpy-self

Root App self wrapper in python.

## Installation

```bash
pip install rootpy-self
```

## Features

- Easy to use Discord.py-inspired API design
- Real-time events via WebSocket support for DM notifications
- Channel polling to monitor all your communities and channels
- Message handling for sending and receiving messages easily
- Profile management for avatar and status updates
- Modular design with clean, organized codebase

## Quick Start

```python
import rootpy

class MyBot(rootpy.RootClient):
    def on_ready(self):
        print("Bot is ready!")
    
    def on_message(self, message):
        print(f"[{message.channel_name}] {message.author_name}: {message.content}")
        
        if message.content == "!ping":
            message.reply("Pong!")

bot = MyBot(token="your_token_here")
bot.run()
```

## Getting Your Token

1. Open the Root app
2. Use a network inspector or packet sniffer to capture API requests
3. Find the `Authorization: Bearer <token>` header
4. Copy the token value

## API Reference

### RootClient

The main client class for interacting with Root.

#### Constructor

```python
RootClient(token, device_id=None)
```

- `token` - Your Root API token
- `device_id` - Optional device ID (auto-generated if not provided)

#### Core Methods

| Method | Description |
|--------|-------------|
| `run(poll_interval=0.1, websocket=False)` | Start the bot and begin listening for events |
| `stop()` | Stop the bot and close all connections |

#### Community & Channel Methods

| Method | Description |
|--------|-------------|
| `get_joined_communities()` | Get a list of all communities you've joined |
| `get_channel_groups(community_id)` | Get all channel groups in a community |
| `get_channels(community_id, channel_group_id)` | Get channels within a specific channel group |
| `get_all_channels(community_id)` | Get all channels in a community (all groups) |
| `add_community(community_id, name)` | Manually add a community to monitor |

#### User Methods

| Method | Description |
|--------|-------------|
| `get_user(user_id, community_id)` | Get user information within a community |

#### Messaging Methods

| Method | Description |
|--------|-------------|
| `send_message(channel_id, content)` | Send a message to a channel |
| `list_messages(channel_id, community_id, limit=3)` | Get recent messages from a channel (max 3) |

#### Profile Methods

| Method | Description |
|--------|-------------|
| `set_avatar(asset_url)` | Set profile picture from an already-uploaded Root asset URL |
| `set_avatar_from_file(file_path)` | Upload a local image file and set it as profile picture |
| `set_avatar_from_url(image_url)` | Download an image from URL, upload it, and set as profile picture |
| `set_status(status_text)` | Set your status text |

#### Upload Methods

| Method | Description |
|--------|-------------|
| `upload_image(file_path)` | Upload a local image file to Root, returns asset URL |
| `upload_image_from_url(url)` | Download and upload an image from URL, returns asset URL |
| `upload_image_bytes(image_data, extension="jpg")` | Upload raw image bytes, returns asset URL |

#### Events

Override these methods to handle events:

```python
def on_ready(self):
    pass

def on_message(self, message):
    pass
```

### Message

Represents a message from Root.

#### Properties

| Property | Type | Description |
|----------|------|-------------|
| `content` | `str` | Message content |
| `author_id` | `tuple` | Author's ID |
| `author_name` | `str` | Author's display name |
| `channel_id` | `tuple` | Channel ID |
| `channel_name` | `str` | Channel name |
| `community_id` | `tuple` | Community ID |
| `community_name` | `str` | Community name |
| `message_id` | `tuple` | Message ID |

#### Methods

| Method | Description |
|--------|-------------|
| `reply(content)` | Reply to the message in the same channel |

## Examples

### Basic Message Logger

```python
import rootpy

class Logger(rootpy.RootClient):
    def on_message(self, message):
        with open("messages.log", "a") as f:
            f.write(f"[{message.community_name}][{message.channel_name}] ")
            f.write(f"{message.author_name}: {message.content}\n")

bot = Logger(token="your_token")
bot.run()
```

### Command Bot with Prefix

```python
import rootpy

class CommandBot(rootpy.RootClient):
    def on_message(self, message):
        if message.content.startswith("!"):
            cmd = message.content[1:].split()[0]
            
            if cmd == "ping":
                message.reply("Pong!")
            elif cmd == "hello":
                message.reply(f"Hello, {message.author_name}!")

bot = CommandBot(token="your_token")
bot.run()
```

### Profile Picture & Status

```python
import rootpy

client = rootpy.RootClient(token="your_token")

client.set_avatar_from_file("my_pic.jpg")

client.set_avatar_from_url("https://example.com/image.png")

client.set_status("Hello World!")

asset_url = client.upload_image("another_pic.png")
if asset_url:
    client.set_avatar(asset_url)
```

## Requirements

- Python 3.8+
- requests
- websocket-client

## License

MIT License

## Disclaimer

This library is for educational purposes only. Use responsibly and in accordance with Root's Terms of Service.
