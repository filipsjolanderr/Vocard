"""Tests for placeholder eval() string escaping."""

import pytest
from voicelink.placeholders import PlayerPlaceholder
from unittest.mock import MagicMock


class TestPlaceholderEval:
    """Test that placeholder eval() properly handles strings with quotes."""
    
    @pytest.fixture
    def mock_bot(self):
        """Create a mock bot."""
        bot = MagicMock()
        bot.user = MagicMock()
        bot.user.display_avatar = MagicMock()
        bot.user.display_avatar.url = "https://example.com/avatar.png"
        return bot
    
    @pytest.fixture
    def placeholder(self, mock_bot):
        """Create a placeholder instance."""
        return PlayerPlaceholder(mock_bot, None)
    
    def test_eval_with_quotes_in_string(self, placeholder):
        """Test that eval() properly handles strings containing quotes."""
        # Test string with apostrophe that caused the original error
        track_name = "Roscoe Dash - All The Way Turnt Up ft. Soulja Boy Tell'em"
        
        variables = {
            "track_name": track_name,
            "track_source_emoji": "🎵"
        }
        
        # Template that uses the track_name in a conditional
        template = "{{@@track_name@@ != 'None' ?? @@track_source_emoji@@ Now Playing: @@track_name@@ // Waiting for song requests}}"
        
        # This should not raise a SyntaxError
        try:
            result = placeholder.replace(template, variables)
            # Should successfully replace the template
            assert "Now Playing:" in result or "Waiting for song requests" in result
        except SyntaxError as e:
            pytest.fail(f"SyntaxError raised when evaluating template with quotes: {e}")
    
    def test_eval_with_double_quotes(self, placeholder):
        """Test that eval() properly handles strings containing double quotes."""
        track_name = 'Song with "quotes" in title'
        
        variables = {
            "track_name": track_name,
            "track_source_emoji": "🎵"
        }
        
        template = "{{@@track_name@@ != 'None' ?? @@track_source_emoji@@ Now Playing: @@track_name@@ // Waiting}}"
        
        try:
            result = placeholder.replace(template, variables)
            assert isinstance(result, str)
        except SyntaxError as e:
            pytest.fail(f"SyntaxError raised when evaluating template with double quotes: {e}")
    
    def test_eval_with_backslashes(self, placeholder):
        """Test that eval() properly handles strings containing backslashes."""
        track_name = "Song\\with\\backslashes"
        
        variables = {
            "track_name": track_name,
            "track_source_emoji": "🎵"
        }
        
        template = "{{@@track_name@@ != 'None' ?? @@track_source_emoji@@ Now Playing: @@track_name@@ // Waiting}}"
        
        try:
            result = placeholder.replace(template, variables)
            assert isinstance(result, str)
        except SyntaxError as e:
            pytest.fail(f"SyntaxError raised when evaluating template with backslashes: {e}")
    
    def test_eval_with_special_characters(self, placeholder):
        """Test that eval() properly handles strings with various special characters."""
        track_name = "Song with 'quotes', \"double quotes\", \\backslashes\\, and more!"
        
        variables = {
            "track_name": track_name,
            "track_source_emoji": "🎵"
        }
        
        template = "{{@@track_name@@ != 'None' ?? @@track_source_emoji@@ Now Playing: @@track_name@@ // Waiting}}"
        
        try:
            result = placeholder.replace(template, variables)
            assert isinstance(result, str)
        except SyntaxError as e:
            pytest.fail(f"SyntaxError raised when evaluating template with special characters: {e}")

