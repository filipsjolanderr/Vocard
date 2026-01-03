"""Tests for optimized update_db function."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from voicelink.mongodb import MongoDBHandler


class TestUpdateDbOptimizations:
    """Test suite for update_db function optimizations."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup for each test."""
        MongoDBHandler._users_buffer.clear()
        MongoDBHandler._last_access.clear()
        MongoDBHandler._users_db = None  # Ensure no actual DB operations
        yield
        MongoDBHandler._users_buffer.clear()
        MongoDBHandler._last_access.clear()

    @pytest.mark.asyncio
    async def test_slice_negative_keeps_last_n(self):
        """Test that negative $slice keeps last N items."""
        user_id = 123456789
        cache = {"_id": user_id, "history": ["old1", "old2", "old3"]}
        db = AsyncMock()
        db.update_one = AsyncMock(return_value=MagicMock(modified_count=1))
        
        # Add 5 new items with $slice: -5 (keep last 5)
        data = {
            "$push": {
                "history": {
                    "$each": ["new1", "new2", "new3", "new4", "new5"],
                    "$slice": -5
                }
            }
        }
        
        result = await MongoDBHandler._update_db(db, cache, {"_id": user_id}, data)
        
        assert result is True
        # Cache should have last 5 items
        assert len(cache["history"]) == 5
        assert cache["history"] == ["old3", "new1", "new2", "new3", "new4", "new5"][-5:]
        
        # MongoDB update should be called with correct structure
        db.update_one.assert_called_once()
        call_args = db.update_one.call_args[0]
        assert "$push" in call_args[1]
        assert call_args[1]["$push"]["history"]["$slice"] == -5

    @pytest.mark.asyncio
    async def test_slice_positive_keeps_first_n(self):
        """Test that positive $slice keeps first N items."""
        user_id = 123456789
        cache = {"_id": user_id, "history": ["old1", "old2"]}
        db = AsyncMock()
        db.update_one = AsyncMock(return_value=MagicMock(modified_count=1))
        
        # Add items with $slice: 3 (keep first 3)
        data = {
            "$push": {
                "history": {
                    "$each": ["new1", "new2"],
                    "$slice": 3
                }
            }
        }
        
        result = await MongoDBHandler._update_db(db, cache, {"_id": user_id}, data)
        
        assert result is True
        # Cache should have first 3 items
        assert len(cache["history"]) == 3
        assert cache["history"] == (["old1", "old2"] + ["new1", "new2"])[:3]

    @pytest.mark.asyncio
    async def test_push_without_slice(self):
        """Test $push without $slice."""
        user_id = 123456789
        cache = {"_id": user_id, "history": ["old1"]}
        db = AsyncMock()
        db.update_one = AsyncMock(return_value=MagicMock(modified_count=1))
        
        data = {
            "$push": {
                "history": "new1"
            }
        }
        
        result = await MongoDBHandler._update_db(db, cache, {"_id": user_id}, data)
        
        assert result is True
        assert cache["history"] == ["old1", "new1"]
        
        # MongoDB update should not have $slice
        call_args = db.update_one.call_args[0]
        assert "$push" in call_args[1]
        assert "$slice" not in call_args[1]["$push"]["history"]

    @pytest.mark.asyncio
    async def test_push_with_each_no_slice(self):
        """Test $push with $each but no $slice."""
        user_id = 123456789
        cache = {"_id": user_id, "history": []}
        db = AsyncMock()
        db.update_one = AsyncMock(return_value=MagicMock(modified_count=1))
        
        data = {
            "$push": {
                "history": {
                    "$each": ["track1", "track2", "track3"]
                }
            }
        }
        
        result = await MongoDBHandler._update_db(db, cache, {"_id": user_id}, data)
        
        assert result is True
        assert cache["history"] == ["track1", "track2", "track3"]
        
        # MongoDB update should have $each but no $slice
        call_args = db.update_one.call_args[0]
        assert "$push" in call_args[1]
        assert "$each" in call_args[1]["$push"]["history"]
        assert "$slice" not in call_args[1]["$push"]["history"]

    @pytest.mark.asyncio
    async def test_slice_history_keeps_25_items(self):
        """Test that history slice keeps exactly 25 items (common use case)."""
        user_id = 123456789
        # Start with 20 items
        cache = {"_id": user_id, "history": [f"old_{i}" for i in range(20)]}
        db = AsyncMock()
        db.update_one = AsyncMock(return_value=MagicMock(modified_count=1))
        
        # Add 10 new items with $slice: -25
        data = {
            "$push": {
                "history": {
                    "$each": [f"new_{i}" for i in range(10)],
                    "$slice": -25
                }
            }
        }
        
        result = await MongoDBHandler._update_db(db, cache, {"_id": user_id}, data)
        
        assert result is True
        # Should have exactly 25 items (last 25)
        assert len(cache["history"]) == 25
        # Should be last 25 items from the combined list
        expected = ([f"old_{i}" for i in range(20)] + [f"new_{i}" for i in range(10)])[-25:]
        assert cache["history"] == expected

    @pytest.mark.asyncio
    async def test_multiple_operations(self):
        """Test multiple update operations in one call."""
        user_id = 123456789
        cache = {"_id": user_id, "history": [], "count": 0}
        db = AsyncMock()
        db.update_one = AsyncMock(return_value=MagicMock(modified_count=1))
        
        data = {
            "$push": {
                "history": {
                    "$each": ["track1"],
                    "$slice": -25
                }
            },
            "$inc": {
                "count": 1
            }
        }
        
        result = await MongoDBHandler._update_db(db, cache, {"_id": user_id}, data)
        
        assert result is True
        assert cache["history"] == ["track1"]
        assert cache["count"] == 1
        
        # MongoDB update should have both operations
        call_args = db.update_one.call_args[0]
        assert "$push" in call_args[1]
        assert "$inc" in call_args[1]

    @pytest.mark.asyncio
    async def test_nested_path_update(self):
        """Test updating nested paths."""
        user_id = 123456789
        cache = {"_id": user_id, "playlist": {}}
        db = AsyncMock()
        db.update_one = AsyncMock(return_value=MagicMock(modified_count=1))
        
        data = {
            "$push": {
                "playlist.200.tracks": "track1"
            }
        }
        
        result = await MongoDBHandler._update_db(db, cache, {"_id": user_id}, data)
        
        assert result is True
        assert cache["playlist"]["200"]["tracks"] == ["track1"]
