"""Tests for translation fallback behavior."""

import pytest
from unittest.mock import MagicMock, patch
from voicelink.placeholders import PlayerPlaceholder
from voicelink.language import LangHandler
from voicelink.player import Player


class TestTranslationFallbacks:
    """Test translation fallback behavior for buttons and messages."""
    
    @pytest.fixture
    def mock_bot(self):
        """Create a mock bot."""
        bot = MagicMock()
        bot.user = MagicMock()
        bot.user.display_avatar = MagicMock()
        bot.user.display_avatar.url = "https://example.com/avatar.png"
        return bot
    
    @pytest.fixture
    def mock_player(self, mock_bot):
        """Create a mock player with proper settings."""
        player = MagicMock(spec=Player)
        player.settings = {"lang": "EN"}
        player.guild = MagicMock()
        player.guild.id = 123456789
        player.volume = 100
        player.queue = MagicMock()
        player.queue.repeat = "Off"
        player.channel = None
        player.current = None
        
        # Mock get_msg to use LangHandler directly
        def get_msg_side_effect(*keys):
            from voicelink.language import LangHandler
            return LangHandler._get_lang(player.settings.get("lang", "EN"), *keys)
        
        player.get_msg = MagicMock(side_effect=get_msg_side_effect)
        return player
    
    @pytest.mark.asyncio
    async def test_translation_with_valid_key(self, mock_bot, mock_player):
        """Test that valid translation keys return the correct translation."""
        # Initialize LangHandler
        LangHandler.init()
        
        # Create placeholder with player
        placeholder = PlayerPlaceholder(mock_bot, mock_player)
        
        # Test valid translation key
        result = placeholder.translation("player.buttons.skip")
        assert result == "Skip"
        
        result = placeholder.translation("player.buttons.autoPlay")
        assert result == "Autoplay"
    
    @pytest.mark.asyncio
    async def test_translation_without_player(self, mock_bot):
        """Test that translation works even without a player."""
        # Initialize LangHandler
        LangHandler.init()
        
        # Create placeholder without player
        placeholder = PlayerPlaceholder(mock_bot, None)
        
        # Test translation should still work with default language
        result = placeholder.translation("player.buttons.skip")
        assert result == "Skip"
        
        result = placeholder.translation("player.buttons.autoPlay")
        assert result == "Autoplay"
    
    @pytest.mark.asyncio
    async def test_translation_with_missing_key(self, mock_bot, mock_player):
        """Test that missing translation keys generate readable fallbacks."""
        # Initialize LangHandler
        LangHandler.init()
        
        # Create placeholder with player
        placeholder = PlayerPlaceholder(mock_bot, mock_player)
        
        # Test missing translation key - should generate fallback
        result = placeholder.translation("player.buttons.nonexistent")
        # Should generate a readable fallback, not "Not found!"
        assert result != "Not found!"
        assert isinstance(result, str)
        assert len(result) > 0
    
    @pytest.mark.asyncio
    async def test_translation_camelcase_fallback(self, mock_bot, mock_player):
        """Test that camelCase keys are converted to readable text."""
        # Initialize LangHandler
        LangHandler.init()
        
        # Create placeholder with player
        placeholder = PlayerPlaceholder(mock_bot, mock_player)
        
        # Test camelCase fallback
        result = placeholder.translation("player.buttons.autoPlay")
        # Should return "Autoplay" (the actual translation)
        assert result == "Autoplay"
        
        # Test with a missing key that has camelCase
        def get_msg_not_found(*keys):
            return "Not found!"
        
        mock_player.get_msg = MagicMock(side_effect=get_msg_not_found)
        result = placeholder.translation("player.buttons.autoPlay")
        # Should convert "autoPlay" -> "Auto Play" (capitalized)
        assert "Auto" in result or "Autoplay" in result
        assert result != "Not found!"
        assert not result.startswith("[")  # Button labels should not have brackets
    
    @pytest.mark.asyncio
    async def test_translation_with_none_lang(self, mock_bot, mock_player):
        """Test that translation works when player lang is None."""
        # Initialize LangHandler
        LangHandler.init()
        
        # Set player lang to None
        mock_player.settings = {"lang": None}
        
        # Create placeholder with player
        placeholder = PlayerPlaceholder(mock_bot, mock_player)
        
        # Test translation should still work with default language
        result = placeholder.translation("player.buttons.skip")
        assert result == "Skip"
        
        result = placeholder.translation("player.buttons.autoPlay")
        assert result == "Autoplay"
    
    @pytest.mark.asyncio
    async def test_translation_with_empty_lang(self, mock_bot, mock_player):
        """Test that translation works when player lang is empty string."""
        # Initialize LangHandler
        LangHandler.init()
        
        # Set player lang to empty string
        mock_player.settings = {"lang": ""}
        
        # Create placeholder with player
        placeholder = PlayerPlaceholder(mock_bot, mock_player)
        
        # Test translation should still work with default language
        result = placeholder.translation("player.buttons.skip")
        assert result == "Skip"
        
        result = placeholder.translation("player.buttons.autoPlay")
        assert result == "Autoplay"
    
    @pytest.mark.asyncio
    async def test_translation_with_invalid_lang(self, mock_bot, mock_player):
        """Test that translation works when player lang is invalid."""
        # Initialize LangHandler
        LangHandler.init()
        
        # Set player lang to invalid value
        mock_player.settings = {"lang": "INVALID"}
        
        # Create placeholder with player
        placeholder = PlayerPlaceholder(mock_bot, mock_player)
        
        # Test translation should fall back to default language
        result = placeholder.translation("player.buttons.skip")
        assert result == "Skip"
        
        result = placeholder.translation("player.buttons.autoPlay")
        assert result == "Autoplay"
    
    @pytest.mark.asyncio
    async def test_button_label_processing(self, mock_bot, mock_player):
        """Test that button labels are processed correctly."""
        # Initialize LangHandler
        LangHandler.init()
        
        # Create placeholder with player
        placeholder = PlayerPlaceholder(mock_bot, mock_player)
        
        # Test button label placeholder format
        label_text = "@@t_player.buttons.skip@@"
        result = placeholder.replace(label_text, {})
        assert result == "Skip"
        
        label_text = "@@t_player.buttons.autoPlay@@"
        result = placeholder.replace(label_text, {})
        assert result == "Autoplay"
        
        # Test with multiple placeholders
        label_text = "@@t_player.buttons.pause@@"
        result = placeholder.replace(label_text, {})
        assert result == "Pause"
    
    @pytest.mark.asyncio
    async def test_all_button_labels_exist(self, mock_bot, mock_player):
        """Test that all button labels in EN.json can be translated."""
        # Initialize LangHandler
        LangHandler.init()
        
        # Create placeholder with player
        placeholder = PlayerPlaceholder(mock_bot, mock_player)
        
        # List of all button labels from EN.json
        button_keys = [
            "player.buttons.back",
            "player.buttons.pause",
            "player.buttons.resume",
            "player.buttons.skip",
            "player.buttons.leave",
            "player.buttons.loop",
            "player.buttons.volumeUp",
            "player.buttons.volumeDown",
            "player.buttons.volumeMute",
            "player.buttons.volumeUnmute",
            "player.buttons.autoPlay",
            "player.buttons.shuffle",
            "player.buttons.forward",
            "player.buttons.rewind",
            "player.buttons.lyrics"
        ]
        
        # Test each button label
        for key in button_keys:
            result = placeholder.translation(key)
            # Should not be "Not found!" or start with "["
            assert result != "Not found!"
            assert not result.startswith("[")
            assert isinstance(result, str)
            assert len(result) > 0

