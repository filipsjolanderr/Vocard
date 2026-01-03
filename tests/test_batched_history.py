"""Tests for batched user history updates."""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch, call
from voicelink.mongodb import MongoDBHandler


class TestBatchedHistoryUpdates:
    """Test suite for batched history update system."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Reset batch state before each test."""
        MongoDBHandler._history_batch.clear()
        if MongoDBHandler._batch_task and not MongoDBHandler._batch_task.done():
            MongoDBHandler._batch_task.cancel()
        MongoDBHandler._batch_task = None
        MongoDBHandler._batch_lock = asyncio.Lock()
        MongoDBHandler._users_db = None  # Ensure no DB operations
        yield
        # Cleanup after test
        if MongoDBHandler._batch_task and not MongoDBHandler._batch_task.done():
            MongoDBHandler._batch_task.cancel()
        MongoDBHandler._history_batch.clear()

    @pytest.mark.asyncio
    async def test_batch_add_history_single_track(self):
        """Test adding a single track to batch."""
        user_id = 123456789
        track_id = "test_track_123"
        
        await MongoDBHandler.batch_add_history(user_id, track_id)
        
        assert user_id in MongoDBHandler._history_batch
        assert MongoDBHandler._history_batch[user_id] == [track_id]

    @pytest.mark.asyncio
    async def test_batch_add_history_multiple_tracks(self):
        """Test adding multiple tracks to batch."""
        user_id = 123456789
        track_ids = [f"track_{i}" for i in range(10)]
        
        for track_id in track_ids:
            await MongoDBHandler.batch_add_history(user_id, track_id)
        
        assert len(MongoDBHandler._history_batch[user_id]) == 10
        assert MongoDBHandler._history_batch[user_id] == track_ids

    @pytest.mark.asyncio
    async def test_batch_flush_at_size_limit(self):
        """Test that batch flushes when size limit is reached."""
        user_id = 123456789
        MongoDBHandler._BATCH_SIZE_LIMIT = 5  # Lower limit for testing
        
        with patch.object(MongoDBHandler, 'update_user', new_callable=AsyncMock) as mock_update:
            # Add tracks up to limit
            for i in range(5):
                await MongoDBHandler.batch_add_history(user_id, f"track_{i}")
            
            # Should have flushed at limit
            mock_update.assert_called_once()
            call_args = mock_update.call_args
            assert call_args[0][0] == user_id
            assert "$push" in call_args[0][1]
            assert call_args[0][1]["$push"]["history"]["$each"] == [f"track_{i}" for i in range(5)]
            assert call_args[0][1]["$push"]["history"]["$slice"] == -25
            
            # Batch should be empty after flush
            assert user_id not in MongoDBHandler._history_batch or not MongoDBHandler._history_batch[user_id]

    @pytest.mark.asyncio
    async def test_batch_flush_interval(self):
        """Test that batch flushes at time interval."""
        user_id = 123456789
        MongoDBHandler._BATCH_FLUSH_INTERVAL = 0.1  # 100ms for testing
        
        with patch.object(MongoDBHandler, 'update_user', new_callable=AsyncMock) as mock_update:
            # Start batch processor
            await MongoDBHandler.start_batch_processor()
            
            # Add a track
            await MongoDBHandler.batch_add_history(user_id, "track_1")
            
            # Wait for flush interval
            await asyncio.sleep(0.15)
            
            # Should have flushed
            mock_update.assert_called()
            
            # Stop processor
            await MongoDBHandler.stop_batch_processor()

    @pytest.mark.asyncio
    async def test_batch_multiple_users(self):
        """Test batching for multiple users independently."""
        user1_id = 111111111
        user2_id = 222222222
        
        await MongoDBHandler.batch_add_history(user1_id, "track_1")
        await MongoDBHandler.batch_add_history(user2_id, "track_2")
        await MongoDBHandler.batch_add_history(user1_id, "track_3")
        
        assert len(MongoDBHandler._history_batch[user1_id]) == 2
        assert len(MongoDBHandler._history_batch[user2_id]) == 1
        assert MongoDBHandler._history_batch[user1_id] == ["track_1", "track_3"]
        assert MongoDBHandler._history_batch[user2_id] == ["track_2"]

    @pytest.mark.asyncio
    async def test_flush_all_history(self):
        """Test flushing all pending history updates."""
        user1_id = 111111111
        user2_id = 222222222
        
        with patch.object(MongoDBHandler, 'update_user', new_callable=AsyncMock) as mock_update:
            await MongoDBHandler.batch_add_history(user1_id, "track_1")
            await MongoDBHandler.batch_add_history(user2_id, "track_2")
            
            await MongoDBHandler.flush_all_history()
            
            # Should have called update_user for both users
            assert mock_update.call_count == 2
            assert user1_id not in MongoDBHandler._history_batch or not MongoDBHandler._history_batch[user1_id]
            assert user2_id not in MongoDBHandler._history_batch or not MongoDBHandler._history_batch[user2_id]

    @pytest.mark.asyncio
    async def test_flush_empty_batch(self):
        """Test flushing when batch is empty."""
        user_id = 123456789
        
        with patch.object(MongoDBHandler, 'update_user', new_callable=AsyncMock) as mock_update:
            await MongoDBHandler._flush_user_history(user_id)
            
            # Should not call update_user for empty batch
            mock_update.assert_not_called()

    @pytest.mark.asyncio
    async def test_batch_processor_start_stop(self):
        """Test starting and stopping batch processor."""
        # Start processor
        await MongoDBHandler.start_batch_processor()
        assert MongoDBHandler._batch_task is not None
        assert not MongoDBHandler._batch_task.done()
        
        # Stop processor
        await MongoDBHandler.stop_batch_processor()
        assert MongoDBHandler._batch_task.done()

    @pytest.mark.asyncio
    async def test_batch_flush_on_shutdown(self):
        """Test that remaining batches are flushed on shutdown."""
        user_id = 123456789
        
        with patch.object(MongoDBHandler, 'update_user', new_callable=AsyncMock) as mock_update:
            await MongoDBHandler.start_batch_processor()
            await MongoDBHandler.batch_add_history(user_id, "track_1")
            await MongoDBHandler.batch_add_history(user_id, "track_2")
            
            # Stop should flush remaining
            await MongoDBHandler.stop_batch_processor()
            
            # Should have flushed
            mock_update.assert_called()
            assert user_id not in MongoDBHandler._history_batch or not MongoDBHandler._history_batch[user_id]

    @pytest.mark.asyncio
    async def test_batch_concurrent_access(self):
        """Test that batch handles concurrent access correctly."""
        user_id = 123456789
        num_tracks = 20
        MongoDBHandler._BATCH_SIZE_LIMIT = 100  # Set high to avoid auto-flush
        
        # Mock the database to prevent errors during flush
        with patch.object(MongoDBHandler, 'update_user', new_callable=AsyncMock):
            # Add tracks concurrently
            tasks = [
                MongoDBHandler.batch_add_history(user_id, f"track_{i}")
                for i in range(num_tracks)
            ]
            await asyncio.gather(*tasks)
            
            # All tracks should be in batch (or flushed if limit reached)
            total_in_batch = len(MongoDBHandler._history_batch.get(user_id, []))
            # Since limit is 100, all 20 should be in batch
            assert total_in_batch == num_tracks
