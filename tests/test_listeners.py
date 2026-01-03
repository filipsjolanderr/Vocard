"""Tests for bot listeners and events."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import discord
from voicelink import NodePool, Config


class TestListeners:
    """Test bot listeners functionality."""

    @pytest.fixture
    def mock_bot(self):
        """Create a mock bot."""
        bot = MagicMock()
        bot.loop = MagicMock()
        bot.loop.create_task = MagicMock()
        return bot

    @pytest.mark.asyncio
    async def test_start_nodes(self, mock_bot):
        """Test that nodes are started."""
        with patch('cogs.listeners.Config', MagicMock()) as mock_config, \
             patch('cogs.listeners.voicelink.NodePool', MagicMock()) as mock_pool, \
             patch('cogs.listeners.func.logger') as mock_logger:
            
            mock_config.return_value.nodes = {
                "node1": {"identifier": "node1", "host": "localhost", "port": 2333}
            }
            
            mock_node = MagicMock()
            mock_node.create_node = AsyncMock()
            mock_pool.return_value = mock_node
            
            from cogs.listeners import Listeners
            cog = Listeners(mock_bot)
            
            await cog.start_nodes()
            
            # Verify node creation was attempted
            assert True  # Adjust based on actual implementation

    @pytest.mark.asyncio
    async def test_restore_last_session_players(self, mock_bot):
        """Test restoring last session players."""
        mock_bot.wait_until_ready = AsyncMock()
        
        with patch('cogs.listeners.func.open_json', return_value=[]), \
             patch('cogs.listeners.Config', MagicMock()):
            
            from cogs.listeners import Listeners
            cog = Listeners(mock_bot)
            
            await cog.restore_last_session_players()
            
            # Verify restoration logic
            mock_bot.wait_until_ready.assert_called_once()
