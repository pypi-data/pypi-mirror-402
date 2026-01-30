# Elara

Elara is an enterprise-grade asynchronous Python wrapper for the Hubber.cc API. Built with performance and simplicity in mind, it provides a clean interface for building powerful bots with minimal code.

## Features

- Fully asynchronous design using asyncio
- Discord.py-style command system with decorators
- Cog system for modular bot organization
- Rich embed builder with method chaining
- Interactive button components
- Advanced caching with LRU/LFU/FIFO eviction policies
- Token bucket rate limiting
- Automatic reconnection with exponential backoff
- Type hints throughout the codebase

## Installation

```bash
pip install hubber.py python-socketio aiohttp
```

## Quick Start

```python
import asyncio
from elara import Client

client = Client("YOUR_BOT_TOKEN", prefix="!")

@client.on("ready")
async def on_ready(data):
    print(f"Bot online as: {data['user']['username']}")

@client.command(name="ping")
async def ping(ctx):
    await ctx.send("Pong!")

asyncio.run(client.run())
```

## Client

### Initialization

```python
Client(token: str, prefix: str = "!", enable_ratelimit: bool = True, enable_cache: bool = True)
```

**Parameters:**
- `token`: Your bot token from Hubber.cc
- `prefix`: Command prefix (default: "!")
- `enable_ratelimit`: Enable automatic rate limiting (default: True)
- `enable_cache`: Enable caching system (default: True)

**Example:**
```python
client = Client("YOUR_TOKEN", prefix=";", enable_ratelimit=True, enable_cache=True)
```

### Methods

#### client.run()
Start the bot and connect to Hubber.cc.

```python
asyncio.run(client.run())
```

#### client.on(event: str)
Register an event listener.

```python
@client.on("message:new")
async def on_message(ctx):
    print(f"{ctx.author.username}: {ctx.content}")
```

#### client.command(name: str, description: str = None, aliases: List[str] = None)
Register a command.

```python
@client.command(name="hello", description="Say hello", aliases=["hi", "hey"])
async def hello(ctx):
    await ctx.send(f"Hello, {ctx.author.username}!")
```

#### client.load_cog(path: str)
Load a cog from a file path.

```python
await client.load_cog("cogs/moderation.py")
```

#### client.unload_cog(cog_name: str)
Unload a loaded cog.

```python
await client.unload_cog("ModerationCog")
```

#### client.reload_cog(cog_name: str)
Reload a cog.

```python
await client.reload_cog("ModerationCog")
```

## Events

### Available Events

- `connect` - Connected to Hubber.cc
- `ready` - Bot is ready and authenticated
- `message:new` - New message received
- `message:edit` - Message was edited
- `message:delete` - Message was deleted
- `interaction:button` - Button was clicked
- `typing:start` - User started typing
- `server:member_join` - Member joined server
- `server:member_leave` - Member left server
- `presence:update` - User presence changed
- `session:expired` - Session token expired (user tokens only)

### Event Examples

```python
@client.on("connect")
async def on_connect():
    print("Connected!")

@client.on("ready")
async def on_ready(data):
    client.user = data["user"]
    print(f"Logged in as {client.user['username']}")

@client.on("message:new")
async def on_message(ctx):
    if "hello" in ctx.content.lower():
        await ctx.send("Hi there!")

@client.on("interaction:button")
async def on_button(ctx):
    if ctx.custom_id == "confirm":
        await ctx.reply("Confirmed!", ephemeral=True)
```

## Context

The Context object is passed to message event handlers and commands.

### Properties

- `ctx.message_id` - Message ID
- `ctx.channel_id` - Channel ID
- `ctx.server_id` - Server ID
- `ctx.user_id` - User ID
- `ctx.content` - Message content
- `ctx.author` - Author object
- `ctx.args` - Command arguments (commands only)
- `ctx.command` - Command object (commands only)

### Methods

#### ctx.send(content: str = None, embed: Embed = None, embeds: List[Embed] = None, components: List[ActionRow] = None)
Send a message to the channel.

```python
await ctx.send("Hello!")
await ctx.send(embed=my_embed)
await ctx.send("Choose:", components=[action_row])
```

#### ctx.reply(content: str = None, embed: Embed = None, embeds: List[Embed] = None, components: List[ActionRow] = None)
Reply to the message.

```python
await ctx.reply("Thanks for your message!")
```

#### ctx.edit(content: str)
Edit the message.

```python
await ctx.edit("Updated content")
```

#### ctx.delete()
Delete the message.

```python
await ctx.delete()
```

#### ctx.react(emoji: str)
Add a reaction to the message.

```python
await ctx.react("👍")
await ctx.react("✅")
```

#### ctx.unreact(emoji: str)
Remove a reaction from the message.

```python
await ctx.unreact("👍")
```

#### ctx.typing()
Show typing indicator in the channel.

```python
await ctx.typing()
```

## Author

The Author object contains information about a user.

### Properties

- `author.id` - User ID
- `author.username` - Username
- `author.avatar` - Avatar path
- `author.avatar_url` - Full avatar URL
- `author.avatar_color` - Avatar color hex
- `author.display_badge` - Display badge
- `author.role_color` - Role color hex

### Example

```python
@client.command(name="userinfo")
async def userinfo(ctx):
    await ctx.send(f"Username: {ctx.author.username}\nID: {ctx.author.id}")
```

## Interaction

The Interaction object is passed to button interaction handlers.

### Properties

- `ctx.custom_id` - Button custom ID
- `ctx.channel_id` - Channel ID
- `ctx.message_id` - Message ID containing the button
- `ctx.interaction_id` - Interaction ID
- `ctx.author` - Author object

### Methods

#### ctx.send(content: str, ephemeral: bool = False)
Send a response to the interaction.

```python
await ctx.send("Button clicked!", ephemeral=True)
```

#### ctx.reply(content: str, ephemeral: bool = False)
Reply to the interaction.

```python
await ctx.reply("Processing...", ephemeral=False)
```

## Commands

### Basic Command

```python
@client.command(name="ping")
async def ping(ctx):
    await ctx.send("Pong!")
```

### Command with Aliases

```python
@client.command(name="info", aliases=["i", "information"])
async def info(ctx):
    await ctx.send("Bot information here")
```

### Command with Arguments

```python
@client.command(name="say")
async def say(ctx):
    if ctx.args:
        await ctx.send(ctx.args)
    else:
        await ctx.send("Please provide text to say")
```

### Command with Description

```python
@client.command(name="help", description="Show help information")
async def help(ctx):
    await ctx.send("Available commands: ping, help, info")
```

## Embeds

Create rich embedded messages with the Embed class.

### Basic Embed

```python
from elara import Embed

embed = Embed(
    title="My Title",
    description="My description",
    color="#5865F2"
)
await ctx.send(embed=embed)
```

### Full Embed Example

```python
embed = Embed(title="User Profile", color="#00FF00")
embed.set_author(name=ctx.author.username, icon_url=ctx.author.avatar_url)
embed.set_description("This is a user profile embed")
embed.add_field(name="Level", value="10", inline=True)
embed.add_field(name="XP", value="1500", inline=True)
embed.set_thumbnail("https://example.com/avatar.png")
embed.set_image("https://example.com/banner.png")
embed.set_footer(text="Profile System", icon_url="https://example.com/icon.png")
embed.set_timestamp()

await ctx.send(embed=embed)
```

### Embed Methods

#### Embed(title: str = None, description: str = None, color: str = None, url: str = None)
Create a new embed.

#### embed.set_author(name: str, icon_url: str = None, url: str = None)
Set the embed author.

#### embed.add_field(name: str, value: str, inline: bool = False)
Add a field to the embed. Maximum 25 fields.

#### embed.set_footer(text: str, icon_url: str = None)
Set the embed footer.

#### embed.set_thumbnail(url: str)
Set the embed thumbnail.

#### embed.set_image(url: str)
Set the embed image.

#### embed.set_timestamp(timestamp: datetime = None)
Set the embed timestamp. Uses current time if not provided.

#### embed.set_color(color: str)
Set the embed color.

### Embed Limits

- Title: 256 characters
- Description: 4,096 characters
- Fields: 25 maximum
- Field Name: 256 characters
- Field Value: 1,024 characters
- Footer: 2,048 characters
- Total: 6,000 characters
- Embeds per message: 10 maximum

## Buttons and Components

Create interactive buttons with ActionRow and Button classes.

### Button Styles

```python
from elara import ButtonStyle

ButtonStyle.PRIMARY    # Blue button
ButtonStyle.SECONDARY  # Gray button
ButtonStyle.SUCCESS    # Green button
ButtonStyle.DANGER     # Red button
ButtonStyle.LINK       # Link button
```

### Basic Buttons

```python
from elara import ActionRow, ButtonStyle

row = ActionRow()
row.add_button("Click Me", ButtonStyle.PRIMARY, custom_id="my_button")
row.add_button("Cancel", ButtonStyle.DANGER, custom_id="cancel")
row.add_button("Website", ButtonStyle.LINK, url="https://example.com")

await ctx.send("Choose an option:", components=[row])
```

### Handling Button Clicks

```python
@client.on("interaction:button")
async def on_button(ctx):
    if ctx.custom_id == "my_button":
        await ctx.reply(f"{ctx.author.username} clicked the button!")
    elif ctx.custom_id == "cancel":
        await ctx.reply("Cancelled", ephemeral=True)
```

### Button Limits

- Maximum 5 action rows per message
- Maximum 5 buttons per action row
- Label: 80 characters maximum
- custom_id: 100 characters maximum
- Link buttons require url, not custom_id

## Cogs

Organize your bot into modular components using cogs.

### Creating a Cog

```python
from elara import Cog, command, listener
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from elara import Client

class MyCog(Cog):
    def __init__(self, client: "Client"):
        self.client = client
        self.description = "My cog description"
        super().__init__(client)
    
    @command(name="test", description="Test command")
    async def test_command(self, ctx):
        await ctx.send("Test successful!")
    
    @listener("message:new")
    async def on_message(self, ctx):
        if "test" in ctx.content:
            await ctx.react("✅")
    
    async def cog_load(self):
        print("Cog loaded!")
    
    async def cog_unload(self):
        print("Cog unloaded!")

async def setup(client: "Client") -> None:
    await client.add_cog(MyCog(client))
```

### Loading Cogs

```python
@client.on("ready")
async def on_ready(data):
    await client.load_cog("cogs/moderation.py")
    await client.load_cog("cogs/fun.py")
```

### Cog Management

```python
await client.load_cog("cogs/music.py")
await client.unload_cog("MusicCog")
await client.reload_cog("MusicCog")
```

### Cog Decorators

#### @command(name: str, description: str = None, aliases: List[str] = None)
Register a command in the cog.

#### @listener(event: str)
Register an event listener in the cog.

## Cache

Advanced caching system with multiple eviction policies.

### Basic Usage

```python
await client.cache.set("key", "value", ttl=60.0)
value = await client.cache.get("key")
await client.cache.delete("key")
await client.cache.clear()
```

### Cache Methods

#### cache.get(key: str)
Get a value from cache.

```python
value = await client.cache.get("user:123")
```

#### cache.set(key: str, value: Any, ttl: float = None)
Set a value in cache with optional TTL.

```python
await client.cache.set("user:123", user_data, ttl=300.0)
```

#### cache.delete(key: str)
Delete a key from cache.

```python
await client.cache.delete("user:123")
```

#### cache.has(key: str)
Check if key exists in cache.

```python
if await client.cache.has("user:123"):
    print("User cached")
```

#### cache.clear()
Clear all cache entries.

```python
await client.cache.clear()
```

#### cache.size()
Get current cache size.

```python
size = client.cache.size()
```

## Rate Limiting

Automatic rate limiting is built-in and enabled by default.

### Rate Limits

- Messages: 5 per 5 seconds
- Channel operations: 2 per 5 seconds

### Disabling Rate Limiting

```python
client = Client("TOKEN", enable_ratelimit=False)
```

## Message Formatting

### User Mentions

```python
await ctx.send(f"Hello <@{ctx.author.id}>!")
```

### Everyone Mention

```python
await ctx.send("@everyone Important announcement!")
```

## Error Handling

### Connection Errors

The client automatically reconnects with exponential backoff:
- 5s, 10s, 30s, 60s, 120s, 300s (max)

### Example Error Handling

```python
@client.command(name="divide")
async def divide(ctx):
    try:
        args = ctx.args.split()
        result = int(args[0]) / int(args[1])
        await ctx.send(f"Result: {result}")
    except (ValueError, IndexError):
        await ctx.send("Usage: !divide <num1> <num2>")
    except ZeroDivisionError:
        await ctx.send("Cannot divide by zero!")
```

## Best Practices

### Use Type Hints

```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from elara import Client
```

### Organize with Cogs

Split your bot into logical modules using cogs for better maintainability.

### Handle Errors Gracefully

Always wrap potentially failing operations in try-except blocks.

### Use Ephemeral Responses

For sensitive information or temporary messages, use ephemeral responses:

```python
await ctx.reply("This is private", ephemeral=True)
```

### Leverage Caching

Cache frequently accessed data to reduce API calls and improve performance.

### Rate Limit Awareness

Keep rate limiting enabled in production to avoid API bans.

## Complete Example

```python
import asyncio
from elara import Client, Embed, ActionRow, ButtonStyle

client = Client("YOUR_TOKEN", prefix="!")

@client.on("ready")
async def on_ready(data):
    print(f"Bot online as: {data['user']['username']}")

@client.command(name="profile", description="View user profile")
async def profile(ctx):
    embed = Embed(
        title=f"{ctx.author.username}'s Profile",
        color="#5865F2"
    )
    embed.set_thumbnail(ctx.author.avatar_url)
    embed.add_field(name="User ID", value=ctx.author.id, inline=True)
    embed.add_field(name="Badge", value=ctx.author.display_badge or "None", inline=True)
    embed.set_footer(text="Profile System")
    embed.set_timestamp()
    
    row = ActionRow()
    row.add_button("Refresh", ButtonStyle.PRIMARY, custom_id="refresh_profile")
    
    await ctx.send(embed=embed, components=[row])

@client.on("interaction:button")
async def on_button(ctx):
    if ctx.custom_id == "refresh_profile":
        await ctx.reply("Profile refreshed!", ephemeral=True)

@client.command(name="ping")
async def ping(ctx):
    await ctx.send("Pong!")

asyncio.run(client.run())
```

## Support

For issues and questions, refer to the Hubber.cc API documentation at https://hubber.cc/docs

## License

This library is provided as-is for use with the Hubber.cc platform.
