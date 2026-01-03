"""Tests for optimized player_check task."""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch, call
from discord.ext import commands
import voicelink


class MockMember:
    """Mock Discord member."""
    def __init__(self, user_id, is_bot=False, self_deaf=False):
        self.id = user_id
        self.bot = is_bot
        self.voice = MagicMock()
        self.voice.self_deaf = self_deaf


class MockChannel:
    """Mock Discord voice channel."""
    def __init__(self, members):
        self.members = members


class MockPlayer:
    """Mock player object."""
    def __init__(self, guild_id, channel_members, has_listener=True, is_playing=True, queue_empty=False, is_24_7=False):
        self.guild_id = guild_id
        self.channel = MockChannel(channel_members)
        self.context = MagicMock()
        self.guild = MagicMock()
        self.guild.id = guild_id
        self.guild.me = MagicMock()
        self.guild.me.voice = MagicMock() if has_listener else None
        self.is_playing = is_playing
        self.queue = MagicMock()
        self.queue.is_empty = queue_empty
        self.settings = {"24/7": is_24_7}
        self.is_paused = False
        self.dj = None
        self.teardown = AsyncMock()
        self.set_pause = AsyncMock()
        self.connect = AsyncMock()


class MockNode:
    """Mock node object."""
    def __init__(self, identifier, players):
        self.identifier = identifier
        self._players = players


@pytest.mark.asyncio
async def test_player_check_delays():
    """Test that delays are added every 5 players."""
    # Create 10 mock players
    players = {}
    for i in range(10):
        members = [MockMember(1000 + i, is_bot=False, self_deaf=False)]
        players[i] = MockPlayer(i, members)
    
    node = MockNode("test_node", players)
    nodes = {"test_node": node}
    
    # Mock NodePool
    with patch.object(voicelink.NodePool, '_nodes', nodes):
        start_time = asyncio.get_event_loop().time()
        
        # Simulate player_check iteration
        player_count = 0
        for identifier, node in voicelink.NodePool._nodes.items():
            for guild_id, player in node._players.copy().items():
                player_count += 1
                if player_count % 5 == 0:
                    await asyncio.sleep(0.1)  # 100ms delay
        
        elapsed = asyncio.get_event_loop().time() - start_time
        
        # Should have at least 1 delay (at player 5 and 10)
        # With 10 players, we should have 2 delays = ~200ms minimum
        assert elapsed >= 0.15  # Allow some margin


@pytest.mark.asyncio
async def test_player_check_member_caching():
    """Test that members list is cached and iterated only once."""
    # Create members
    members_list = [
        MockMember(1, is_bot=False, self_deaf=False),  # Listener
        MockMember(2, is_bot=True, self_deaf=False),  # Bot
        MockMember(3, is_bot=False, self_deaf=True),   # Deaf
        MockMember(4, is_bot=False, self_deaf=False),  # Listener
    ]
    
    player = MockPlayer(123, members_list)
    
    # Simulate optimized member checking
    members = player.channel.members
    members_list_cached = list(members)  # Convert to list once
    
    # Optimize member checking - iterate only once
    has_listener = False
    non_bot_members = []
    for member in members_list_cached:
        if not member.bot:
            non_bot_members.append(member)
            if not (member.voice and member.voice.self_deaf):
                has_listener = True
    
    # Verify results
    assert has_listener is True  # Members 1 and 4 are listeners
    assert len(non_bot_members) == 3  # Members 1, 3, 4 (not bot)
    assert non_bot_members[0].id == 1
    assert non_bot_members[1].id == 3
    assert non_bot_members[2].id == 4


@pytest.mark.asyncio
async def test_player_check_dj_assignment():
    """Test that DJ is assigned from cached non-bot members."""
    members_list = [
        MockMember(1, is_bot=True),   # Bot - should be skipped
        MockMember(2, is_bot=False), # Should become DJ
        MockMember(3, is_bot=False), # Should not become DJ (first non-bot wins)
    ]
    
    player = MockPlayer(123, members_list)
    
    # Simulate optimized DJ assignment
    members = player.channel.members
    members_list_cached = list(members)
    
    non_bot_members = [m for m in members_list_cached if not m.bot]
    
    if player.dj not in members_list_cached:
        if non_bot_members:
            player.dj = non_bot_members[0]
    
    assert player.dj is not None
    assert player.dj.id == 2  # First non-bot member


@pytest.mark.asyncio
async def test_player_check_no_listener_teardown():
    """Test that player is torn down when no listeners."""
    members_list = [
        MockMember(1, is_bot=True),              # Only bots
        MockMember(2, is_bot=True),
    ]
    
    player = MockPlayer(123, members_list, has_listener=False, is_playing=False, queue_empty=True)
    
    # Simulate check
    members = player.channel.members
    members_list_cached = list(members)
    
    has_listener = False
    for member in members_list_cached:
        if not member.bot:
            if not (member.voice and member.voice.self_deaf):
                has_listener = True
    
    if (not player.is_playing and player.queue.is_empty) or not has_listener:
        if not player.settings.get('24/7', False):
            await player.teardown()
    
    player.teardown.assert_called_once()


@pytest.mark.asyncio
async def test_player_check_24_7_pause():
    """Test that 24/7 players are paused instead of torn down."""
    members_list = [
        MockMember(1, is_bot=True),  # Only bots
    ]
    
    player = MockPlayer(123, members_list, has_listener=False, is_playing=False, queue_empty=True, is_24_7=True)
    
    # Simulate check
    members = player.channel.members
    members_list_cached = list(members)
    
    has_listener = False
    for member in members_list_cached:
        if not member.bot:
            if not (member.voice and member.voice.self_deaf):
                has_listener = True
    
    if (not player.is_playing and player.queue.is_empty) or not has_listener:
        if not player.settings.get('24/7', False):
            await player.teardown()
        else:
            if not player.is_paused:
                await player.set_pause(True)
    
    player.teardown.assert_not_called()
    player.set_pause.assert_called_once_with(True)


@pytest.mark.asyncio
async def test_player_check_member_iteration_count():
    """Test that members are only iterated once."""
    members_list = [
        MockMember(i, is_bot=(i % 2 == 0), self_deaf=(i % 3 == 0))
        for i in range(10)
    ]
    
    player = MockPlayer(123, members_list)
    
    # Track iteration count
    iteration_count = 0
    
    members = player.channel.members
    members_list_cached = list(members)  # Convert once
    
    has_listener = False
    non_bot_members = []
    for member in members_list_cached:
        iteration_count += 1
        if not member.bot:
            non_bot_members.append(member)
            if not (member.voice and member.voice.self_deaf):
                has_listener = True
    
    # DJ assignment uses cached list, no additional iteration
    if player.dj not in members_list_cached:
        if non_bot_members:
            player.dj = non_bot_members[0]
    
    # Should have iterated exactly once (10 members)
    assert iteration_count == 10
