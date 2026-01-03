"""Tests for shutdown cleanup functionality."""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from voicelink.mongodb import MongoDBHandler


class TestShutdownCleanup:
    """Test suite for shutdown cleanup."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup for each test."""
        MongoDBHandler._history_batch.clear()
        if MongoDBHandler._batch_task and not MongoDBHandler._batch_task.done():
            MongoDBHandler._batch_task.cancel()
        MongoDBHandler._batch_task = None
        MongoDBHandler._batch_lock = asyncio.Lock()
        MongoDBHandler._users_db = None  # Ensure no DB operations
        yield
        # Cleanup
        if MongoDBHandler._batch_task and not MongoDBHandler._batch_task.done():
            MongoDBHandler._batch_task.cancel()
        MongoDBHandler._history_batch.clear()

    @pytest.mark.asyncio
    async def test_stop_batch_processor_flushes_remaining(self):
        """Test that stop_batch_processor flushes remaining updates."""
        user1_id = 111111111
        user2_id = 222222222
        
        with patch.object(MongoDBHandler, 'update_user', new_callable=AsyncMock) as mock_update:
            # Add some tracks to batch
            await MongoDBHandler.batch_add_history(user1_id, "track_1")
            await MongoDBHandler.batch_add_history(user1_id, "track_2")
            await MongoDBHandler.batch_add_history(user2_id, "track_3")
            
            # Start processor
            await MongoDBHandler.start_batch_processor()
            
            # Stop should flush all remaining
            await MongoDBHandler.stop_batch_processor()
            
            # Should have flushed all users
            assert mock_update.call_count >= 2  # At least 2 users
            assert user1_id not in MongoDBHandler._history_batch or not MongoDBHandler._history_batch[user1_id]
            assert user2_id not in MongoDBHandler._history_batch or not MongoDBHandler._history_batch[user2_id]

    @pytest.mark.asyncio
    async def test_stop_batch_processor_cancels_task(self):
        """Test that stop_batch_processor properly cancels the background task."""
        await MongoDBHandler.start_batch_processor()
        assert MongoDBHandler._batch_task is not None
        assert not MongoDBHandler._batch_task.done()
        
        await MongoDBHandler.stop_batch_processor()
        
        assert MongoDBHandler._batch_task.done()

    @pytest.mark.asyncio
    async def test_flush_all_on_cancellation(self):
        """Test that cancellation triggers flush."""
        user_id = 123456789
        MongoDBHandler._BATCH_FLUSH_INTERVAL = 0.5  # 500ms
        
        with patch.object(MongoDBHandler, 'update_user', new_callable=AsyncMock) as mock_update:
            await MongoDBHandler.start_batch_processor()
            await MongoDBHandler.batch_add_history(user_id, "track_1")
            
            # Wait a bit
            await asyncio.sleep(0.1)
            
            # Stop (which cancels and flushes)
            await MongoDBHandler.stop_batch_processor()
            
            # Should have flushed
            mock_update.assert_called()

    @pytest.mark.asyncio
    async def test_multiple_stop_calls_safe(self):
        """Test that calling stop multiple times is safe."""
        await MongoDBHandler.start_batch_processor()
        
        # First stop
        await MongoDBHandler.stop_batch_processor()
        
        # Second stop should not raise error
        await MongoDBHandler.stop_batch_processor()
        
        # Third stop should also be safe
        await MongoDBHandler.stop_batch_processor()

    @pytest.mark.asyncio
    async def test_flush_empty_on_shutdown(self):
        """Test that flushing empty batch on shutdown doesn't error."""
        # Start and stop with no data
        await MongoDBHandler.start_batch_processor()
        
        with patch.object(MongoDBHandler, 'update_user', new_callable=AsyncMock) as mock_update:
            await MongoDBHandler.stop_batch_processor()
            
            # Should not have called update_user (no data to flush)
            # But the call itself should not error
            assert True  # If we get here, no error occurred
