"""Tests for basic music commands."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import discord
from discord.ext import commands
import voicelink


class TestPlayCommand:
    """Test play command functionality."""

    @pytest.fixture
    def mock_ctx(self):
        """Create a mock command context."""
        ctx = MagicMock(spec=commands.Context)
        ctx.author = MagicMock()
        ctx.author.id = 123456789
        ctx.author.mention = "<@123456789>"
        ctx.guild = MagicMock()
        ctx.guild.id = 987654321
        ctx.guild.voice_client = None
        ctx.interaction = None
        ctx.mention = "<@123456789>"
        return ctx

    @pytest.fixture
    def mock_player(self):
        """Create a mock player."""
        player = MagicMock(spec=voicelink.Player)
        player.channel = MagicMock()
        player.channel.mention = "<#111222333>"
        player.is_user_join = MagicMock(return_value=True)
        player.get_tracks = AsyncMock()
        player.add_track = AsyncMock(return_value=0)
        player.is_playing = False
        player.do_next = AsyncMock()
        return player

    @pytest.mark.asyncio
    async def test_play_creates_player_if_none(self, mock_ctx, mock_player):
        """Test that play command creates player if none exists."""
        mock_track = MagicMock()
        mock_track.title = "Test Song"
        mock_track.uri = "https://example.com/track"
        mock_track.author = "Test Artist"
        mock_track.formatted_length = "3:00"
        mock_track.is_stream = False
        
        with patch('cogs.basic.voicelink.connect_channel', new_callable=AsyncMock) as mock_connect, \
             patch('cogs.basic.send_localized_message', new_callable=AsyncMock), \
             patch('cogs.basic.dispatch_message', new_callable=AsyncMock), \
             patch('cogs.basic.LangHandler.get_lang', new_callable=AsyncMock) as mock_lang:
            
            mock_connect.return_value = mock_player
            mock_player.get_tracks = AsyncMock(return_value=[mock_track])
            mock_lang.return_value = ["", "Position: {}", "Now playing: {}"]
            
            from cogs.basic import Basic
            cog = Basic(MagicMock())
            
            # Call the command method directly (not through Discord.py command system)
            await cog.play.callback(cog, mock_ctx, query="test query")
            
            mock_connect.assert_called_once()

    @pytest.mark.asyncio
    async def test_play_checks_user_in_channel(self, mock_ctx, mock_player):
        """Test that play checks if user is in channel."""
        mock_ctx.guild.voice_client = mock_player
        mock_player.is_user_join = MagicMock(return_value=False)
        
        with patch('cogs.basic.send_localized_message', new_callable=AsyncMock) as mock_send:
            from cogs.basic import Basic
            cog = Basic(MagicMock())
            
            # Call the command method directly
            await cog.play.callback(cog, mock_ctx, query="test query")
            
            mock_send.assert_called()
            mock_player.get_tracks.assert_not_called()

    @pytest.mark.asyncio
    async def test_play_handles_no_tracks(self, mock_ctx, mock_player):
        """Test play command when no tracks are found."""
        mock_ctx.guild.voice_client = mock_player
        mock_player.get_tracks = AsyncMock(return_value=None)
        
        with patch('cogs.basic.send_localized_message', new_callable=AsyncMock) as mock_send:
            from cogs.basic import Basic
            cog = Basic(MagicMock())
            
            # Call the command method directly
            await cog.play.callback(cog, mock_ctx, query="invalid query")
            
            mock_send.assert_called()

    @pytest.mark.asyncio
    async def test_play_handles_playlist(self, mock_ctx, mock_player):
        """Test play command with playlist."""
        mock_ctx.guild.voice_client = mock_player
        
        mock_playlist = MagicMock()
        mock_playlist.name = "Test Playlist"
        mock_playlist.tracks = [MagicMock(), MagicMock()]
        
        mock_player.get_tracks = AsyncMock(return_value=mock_playlist)
        mock_player.add_track = AsyncMock(return_value=2)
        
        with patch('cogs.basic.send_localized_message', new_callable=AsyncMock) as mock_send, \
             patch('cogs.basic.MongoDBHandler.get_settings', new_callable=AsyncMock, return_value={}), \
             patch('cogs.basic.LangHandler.get_lang', new_callable=AsyncMock, return_value="Playlist loaded"):
            from cogs.basic import Basic
            cog = Basic(MagicMock())
            
            # Call the command method directly
            await cog.play.callback(cog, mock_ctx, query="playlist url")
            
            # Should have called send_localized_message or add_track
            assert mock_send.called or mock_player.add_track.called


class TestPauseResumeCommands:
    """Test pause and resume commands."""

    @pytest.fixture
    def mock_ctx(self):
        """Create a mock command context."""
        ctx = MagicMock(spec=commands.Context)
        ctx.author = MagicMock()
        ctx.guild = MagicMock()
        ctx.guild.voice_client = None
        return ctx

    @pytest.fixture
    def mock_player(self):
        """Create a mock player."""
        player = MagicMock(spec=voicelink.Player)
        player.is_privileged = MagicMock(return_value=True)
        player.is_paused = False
        player.set_pause = AsyncMock()
        return player

    @pytest.mark.asyncio
    async def test_pause_requires_player(self, mock_ctx):
        """Test that pause requires a player."""
        with patch('cogs.basic.send_localized_message', new_callable=AsyncMock) as mock_send:
            from cogs.basic import Basic
            cog = Basic(MagicMock())
            
            # Call the command method directly
            await cog.pause.callback(cog, mock_ctx)
            
            mock_send.assert_called()

    @pytest.mark.asyncio
    async def test_pause_requires_privileges(self, mock_ctx, mock_player):
        """Test that pause requires privileges."""
        mock_ctx.guild.voice_client = mock_player
        mock_player.is_privileged = MagicMock(return_value=False)
        mock_player.is_paused = False
        mock_player.pause_votes = set()  # Ensure it's a set
        mock_player.required = MagicMock(return_value=2)  # Return int
        
        with patch('cogs.basic.send_localized_message', new_callable=AsyncMock) as mock_send:
            from cogs.basic import Basic
            cog = Basic(MagicMock())
            
            # Call the command method directly
            await cog.pause.callback(cog, mock_ctx)
            
            # Should send a vote message
            assert mock_send.called

    @pytest.mark.asyncio
    async def test_pause_toggles_pause(self, mock_ctx, mock_player):
        """Test that pause toggles pause state."""
        mock_ctx.guild.voice_client = mock_player
        mock_player.is_paused = False
        mock_player.controls = MagicMock()
        mock_player.controls.pause = MagicMock()
        mock_player.controls.pause.success = "Paused"
        
        with patch('cogs.basic.send_localized_message', new_callable=AsyncMock):
            from cogs.basic import Basic
            cog = Basic(MagicMock())
            
            # Call the command method directly
            await cog.pause.callback(cog, mock_ctx)
            
            # set_pause is called with True and author
            assert mock_player.set_pause.called
            call_args = mock_player.set_pause.call_args[0]
            assert call_args[0] is True

    @pytest.mark.asyncio
    async def test_resume_toggles_pause(self, mock_ctx, mock_player):
        """Test that resume toggles pause state."""
        mock_ctx.guild.voice_client = mock_player
        mock_player.is_paused = True
        
        with patch('cogs.basic.send_localized_message', new_callable=AsyncMock):
            from cogs.basic import Basic
            cog = Basic(MagicMock())
            
            # Call the command method directly
            await cog.resume.callback(cog, mock_ctx)
            
            # set_pause may be called with author as second arg
            assert mock_player.set_pause.called
            # Check that False was passed as first argument
            call_args = mock_player.set_pause.call_args[0]
            assert call_args[0] is False


class TestSkipCommand:
    """Test skip command functionality."""

    @pytest.fixture
    def mock_ctx(self):
        """Create a mock command context."""
        ctx = MagicMock(spec=commands.Context)
        ctx.author = MagicMock()
        ctx.guild = MagicMock()
        ctx.guild.voice_client = None
        return ctx

    @pytest.fixture
    def mock_player(self):
        """Create a mock player."""
        player = MagicMock(spec=voicelink.Player)
        player.is_privileged = MagicMock(return_value=True)
        player.skip = AsyncMock()
        player.current = MagicMock()
        # Create a proper queue mock
        queue_mock = MagicMock()
        queue_mock._repeat = MagicMock()
        queue_mock._repeat.mode = MagicMock()
        queue_mock.skipto = MagicMock()
        player.queue = queue_mock
        player.node = MagicMock()
        player.node._available = True
        player.stop = AsyncMock()
        player.required = MagicMock(return_value=1)
        return player

    @pytest.mark.asyncio
    async def test_skip_requires_player(self, mock_ctx):
        """Test that skip requires a player."""
        with patch('cogs.basic.send_localized_message', new_callable=AsyncMock) as mock_send:
            from cogs.basic import Basic
            cog = Basic(MagicMock())
            
            # Call the command method directly
            await cog.skip.callback(cog, mock_ctx)
            
            mock_send.assert_called()

    @pytest.mark.asyncio
    async def test_skip_calls_player_skip(self, mock_ctx, mock_player):
        """Test that skip calls player.skip()."""
        mock_ctx.guild.voice_client = mock_player
        mock_player.is_playing = True
        mock_player.current = MagicMock()
        mock_player.current.requester = MagicMock()
        mock_player.skip_votes = set()
        mock_player.queue._repeat = MagicMock()
        mock_player.queue._repeat.mode = MagicMock()
        mock_player.stop = AsyncMock()
        
        with patch('cogs.basic.send_localized_message', new_callable=AsyncMock), \
             patch('cogs.basic.voicelink.LoopType', MagicMock()):
            from cogs.basic import Basic
            cog = Basic(MagicMock())
            
            # Call the command method directly
            await cog.skip.callback(cog, mock_ctx)
            
            # stop() is called, not skip()
            assert mock_player.stop.called


class TestQueueCommands:
    """Test queue-related commands."""

    @pytest.fixture
    def mock_ctx(self):
        """Create a mock command context."""
        ctx = MagicMock(spec=commands.Context)
        ctx.author = MagicMock()
        ctx.guild = MagicMock()
        ctx.guild.voice_client = None
        return ctx

    @pytest.fixture
    def mock_player(self):
        """Create a mock player."""
        player = MagicMock(spec=voicelink.Player)
        player.queue = MagicMock()
        player.queue.tracks = MagicMock(return_value=[])
        player.queue.is_empty = True
        return player

    @pytest.mark.asyncio
    async def test_clear_requires_player(self, mock_ctx):
        """Test that clear requires a player."""
        with patch('cogs.basic.send_localized_message', new_callable=AsyncMock) as mock_send:
            from cogs.basic import Basic
            cog = Basic(MagicMock())
            
            # Call the command method directly
            await cog.clear.callback(cog, mock_ctx)
            
            mock_send.assert_called()

    @pytest.mark.asyncio
    async def test_clear_clears_queue(self, mock_ctx, mock_player):
        """Test that clear clears the queue."""
        mock_ctx.guild.voice_client = mock_player
        mock_player.is_privileged = MagicMock(return_value=True)
        mock_player.clear_queue = AsyncMock()  # clear_queue is the method, not queue.clear
        
        with patch('cogs.basic.send_localized_message', new_callable=AsyncMock):
            from cogs.basic import Basic
            cog = Basic(MagicMock())
            
            # Call the command method directly
            await cog.clear.callback(cog, mock_ctx)
            
            # clear_queue is called with queue type and author
            assert mock_player.clear_queue.called
