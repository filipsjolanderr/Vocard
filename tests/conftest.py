"""Pytest configuration and fixtures."""
import pytest
import asyncio
import os
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any
import discord
from discord.ext import commands

# Mock settings.json before any imports that require it
@pytest.fixture(scope="session", autouse=True)
def mock_settings_file():
    """Mock settings.json file existence."""
    mock_settings = {
        "client_id": 0,
        "token": "test_token",
        "mongodb_url": "mongodb://test",
        "mongodb_name": "test_db",
        "bot_prefix": "!",
        "embed_color": "0xb3b3b3",  # Must be string for hex conversion
        "invite_link": "https://example.com",
        "ipc_client": {"enable": False},
        "logging": {"file": {"enable": False}, "level": {}},
        "version": "1.0.0",
        "nodes": {},
        "activity": [],
        "default_max_queue": 1000,
        "default_search_platform": "youtube",
        "lyrics_platform": "lrclib",
        "playlist_settings": {"max_playlist": 5, "max_tracks_per_playlist": 500},
        "sources_settings": {},
        "default_controller": {},
        "default_voice_status_template": "",
        "cooldowns": {},
        "aliases": {},
        "bot_access_user": []
    }
    with patch('os.path.exists', return_value=True), \
         patch('function.open_json', return_value=mock_settings), \
         patch('os.getenv', return_value="0"):
        yield


@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_mongodb_collection():
    """Mock MongoDB collection."""
    collection = AsyncMock()
    collection.update_one = AsyncMock(return_value=MagicMock(modified_count=1))
    collection.find_one = AsyncMock(return_value=None)
    collection.insert_one = AsyncMock()
    return collection


@pytest.fixture
def mock_user_data():
    """Mock user data structure."""
    return {
        "_id": 123456789,
        "playlist": {
            "200": {
                "tracks": [],
                "perms": {"read": [], "write": [], "remove": []},
                "name": "Favourite",
                "type": "playlist",
            }
        },
        "history": [],
        "inbox": [],
    }


@pytest.fixture
def mock_guild():
    """Mock Discord guild."""
    guild = MagicMock(spec=discord.Guild)
    guild.id = 987654321
    guild.name = "Test Guild"
    guild.me = MagicMock()
    guild.me.display_avatar = MagicMock()
    guild.me.display_avatar.url = "https://example.com/avatar.png"
    return guild


@pytest.fixture
def mock_member():
    """Mock Discord member."""
    member = MagicMock(spec=discord.Member)
    member.id = 123456789
    member.name = "TestUser"
    member.display_name = "TestUser"
    member.bot = False
    member.mention = "<@123456789>"
    member.guild_permissions = MagicMock()
    member.guild_permissions.manage_guild = True
    return member


@pytest.fixture
def mock_channel():
    """Mock Discord channel."""
    channel = MagicMock(spec=discord.TextChannel)
    channel.id = 111222333
    channel.name = "test-channel"
    channel.send = AsyncMock()
    channel.permissions_for = MagicMock(return_value=MagicMock(
        read_messages=True,
        send_messages=True
    ))
    return channel


@pytest.fixture
def mock_voice_channel():
    """Mock Discord voice channel."""
    channel = MagicMock(spec=discord.VoiceChannel)
    channel.id = 444555666
    channel.name = "test-voice"
    channel.members = []
    return channel


@pytest.fixture
def mock_message(mock_guild, mock_member, mock_channel):
    """Mock Discord message."""
    message = MagicMock(spec=discord.Message)
    message.id = 777888999
    message.content = "test message"
    message.author = mock_member
    message.guild = mock_guild
    message.channel = mock_channel
    message.attachments = []
    message.mention_everyone = False
    message.delete = AsyncMock()
    return message


@pytest.fixture
def mock_interaction(mock_guild, mock_member, mock_channel):
    """Mock Discord interaction."""
    interaction = MagicMock(spec=discord.Interaction)
    interaction.id = 111222333
    interaction.user = mock_member
    interaction.guild = mock_guild
    interaction.channel = mock_channel
    interaction.response = MagicMock()
    interaction.response.defer = AsyncMock()
    interaction.response.send_message = AsyncMock()
    interaction.type = discord.InteractionType.application_command
    return interaction


@pytest.fixture
def mock_context(mock_guild, mock_member, mock_channel):
    """Mock command context."""
    ctx = MagicMock(spec=commands.Context)
    ctx.message = MagicMock()
    ctx.author = mock_member
    ctx.guild = mock_guild
    ctx.channel = mock_channel
    ctx.prefix = "!"
    ctx.command = MagicMock()
    ctx.command.name = "test"
    ctx.command.parent = None
    ctx.command.signature = ""
    ctx.command.aliases = []
    ctx.command.help = "Test command"
    ctx.interaction = None
    ctx.reply = AsyncMock()
    ctx.send = AsyncMock()
    ctx.me = MagicMock()
    ctx.me.display_avatar = MagicMock()
    ctx.me.display_avatar.url = "https://example.com/avatar.png"
    ctx.current_parameter = None
    return ctx
