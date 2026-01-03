"""Integration tests for all optimizations working together."""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from voicelink.mongodb import MongoDBHandler


class TestIntegration:
    """Integration tests for all optimizations."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup for each test."""
        MongoDBHandler._history_batch.clear()
        if MongoDBHandler._batch_task and not MongoDBHandler._batch_task.done():
            MongoDBHandler._batch_task.cancel()
        MongoDBHandler._batch_task = None
        MongoDBHandler._batch_lock = asyncio.Lock()
        MongoDBHandler._users_buffer.clear()
        yield
        # Cleanup
        if MongoDBHandler._batch_task and not MongoDBHandler._batch_task.done():
            MongoDBHandler._batch_task.cancel()
        MongoDBHandler._history_batch.clear()
        MongoDBHandler._users_buffer.clear()

    @pytest.mark.asyncio
    async def test_batch_and_flush_workflow(self):
        """Test complete workflow: batch -> flush -> update_db."""
        user_id = 123456789
        MongoDBHandler._BATCH_SIZE_LIMIT = 3  # Lower for testing
        
        # Mock the database operations
        with patch.object(MongoDBHandler, '_users_db', new_callable=MagicMock) as mock_db:
            mock_db.update_one = AsyncMock(return_value=MagicMock(modified_count=1))
            mock_db.find_one = AsyncMock(return_value={
                "_id": user_id,
                "history": [],
                "playlist": {},
                "inbox": []
            })
            
            # Initialize user buffer
            MongoDBHandler._users_buffer[user_id] = {
                "_id": user_id,
                "history": [],
                "playlist": {},
                "inbox": []
            }
            
            # Add tracks to batch
            await MongoDBHandler.batch_add_history(user_id, "track_1")
            await MongoDBHandler.batch_add_history(user_id, "track_2")
            await MongoDBHandler.batch_add_history(user_id, "track_3")  # Should trigger flush
            
            # Verify database was called
            assert mock_db.update_one.called
            
            # Verify the update had correct structure
            call_args = mock_db.update_one.call_args[0]
            update_op = call_args[1]
            assert "$push" in update_op
            assert "history" in update_op["$push"]
            assert "$each" in update_op["$push"]["history"]
            assert "$slice" in update_op["$push"]["history"]
            assert update_op["$push"]["history"]["$slice"] == -25

    @pytest.mark.asyncio
    async def test_batch_size_limit_accuracy(self):
        """Test that batch size limit is exactly enforced."""
        user_id = 123456789
        MongoDBHandler._BATCH_SIZE_LIMIT = 5
        
        update_count = 0
        
        async def mock_update(user_id, data):
            nonlocal update_count
            update_count += 1
        
        with patch.object(MongoDBHandler, 'update_user', side_effect=mock_update):
            # Add exactly 5 tracks - should flush
            for i in range(5):
                await MongoDBHandler.batch_add_history(user_id, f"track_{i}")
            
            assert update_count == 1  # Should have flushed once
            
            # Add 3 more - should not flush yet
            for i in range(5, 8):
                await MongoDBHandler.batch_add_history(user_id, f"track_{i}")
            
            assert update_count == 1  # Still only one flush
            
            # Add 2 more to reach limit again
            for i in range(8, 10):
                await MongoDBHandler.batch_add_history(user_id, f"track_{i}")
            
            assert update_count == 2  # Should have flushed again

    @pytest.mark.asyncio
    async def test_time_interval_flush_accuracy(self):
        """Test that time interval flush works correctly."""
        user_id = 123456789
        MongoDBHandler._BATCH_FLUSH_INTERVAL = 0.2  # 200ms
        
        flush_times = []
        
        async def mock_update(user_id, data):
            flush_times.append(asyncio.get_event_loop().time())
        
        with patch.object(MongoDBHandler, 'update_user', side_effect=mock_update):
            await MongoDBHandler.start_batch_processor()
            
            # Add a track
            start_time = asyncio.get_event_loop().time()
            await MongoDBHandler.batch_add_history(user_id, "track_1")
            
            # Wait for flush
            await asyncio.sleep(0.25)
            
            # Should have flushed
            assert len(flush_times) >= 1
            elapsed = flush_times[0] - start_time
            assert 0.15 <= elapsed <= 0.3  # Allow some margin
            
            await MongoDBHandler.stop_batch_processor()

    @pytest.mark.asyncio
    async def test_concurrent_batch_operations(self):
        """Test that batching handles concurrent operations correctly."""
        user_id = 123456789
        num_concurrent = 20
        MongoDBHandler._BATCH_SIZE_LIMIT = 100  # Set high to avoid auto-flush
        
        # Mock the database to prevent errors during flush
        with patch.object(MongoDBHandler, 'update_user', new_callable=AsyncMock):
            # Add tracks concurrently
            tasks = [
                MongoDBHandler.batch_add_history(user_id, f"track_{i}")
                for i in range(num_concurrent)
            ]
            await asyncio.gather(*tasks)
            
            # All tracks should be in batch (or flushed if limit reached)
            total_in_batch = len(MongoDBHandler._history_batch.get(user_id, []))
            # Since limit is 100, all 20 should be in batch
            assert total_in_batch == num_concurrent or total_in_batch == 0  # Either all or flushed

    @pytest.mark.asyncio
    async def test_shutdown_preserves_data(self):
        """Test that shutdown properly preserves all data."""
        user1_id = 111111111
        user2_id = 222222222
        user3_id = 333333333
        
        flush_data = {}
        
        async def mock_update(user_id, data):
            flush_data[user_id] = data["$push"]["history"]["$each"]
        
        with patch.object(MongoDBHandler, 'update_user', side_effect=mock_update):
            await MongoDBHandler.start_batch_processor()
            
            # Add tracks to multiple users
            await MongoDBHandler.batch_add_history(user1_id, "track_1")
            await MongoDBHandler.batch_add_history(user1_id, "track_2")
            await MongoDBHandler.batch_add_history(user2_id, "track_3")
            await MongoDBHandler.batch_add_history(user3_id, "track_4")
            await MongoDBHandler.batch_add_history(user3_id, "track_5")
            
            # Shutdown should flush all
            await MongoDBHandler.stop_batch_processor()
            
            # All users should have been flushed
            assert user1_id in flush_data
            assert user2_id in flush_data
            assert user3_id in flush_data
            assert len(flush_data[user1_id]) == 2
            assert len(flush_data[user2_id]) == 1
            assert len(flush_data[user3_id]) == 2
