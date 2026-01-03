# Comprehensive Bot Test Suite

This document describes the comprehensive test suite for the entire Vocard bot.

## Test Structure

### Core Bot Tests (`test_bot_core.py`)

- Bot initialization and setup
- Message handling
- Command error handling
- Prefix handling
- Event handlers

### Basic Commands Tests (`test_basic_commands.py`)

- Play command
- Pause/Resume commands
- Skip command
- Queue management commands
- Search functionality

### Settings Commands Tests (`test_settings_commands.py`)

- Prefix settings
- Language settings
- Permission checks

### Playlist Commands Tests (`test_playlist_commands.py`)

- List playlists
- Create playlists
- Manage playlists

### Listeners Tests (`test_listeners.py`)

- Node connection
- Session restoration

## Running Tests

```bash
# Run all bot tests
pytest tests/test_bot_*.py -v

# Run specific test file
pytest tests/test_bot_core.py -v

# Run with coverage
pytest tests/ --cov=. --cov-report=html
```

## Test Coverage Goals

- ✅ Bot initialization
- ✅ Message handling
- ✅ Command processing
- ✅ Error handling
- ✅ Settings management
- ✅ Music commands
- ✅ Playlist management
- ✅ Event listeners

## Notes

- Tests use extensive mocking to avoid requiring actual Discord/MongoDB connections
- Settings.json is mocked to prevent file system dependencies
- All async operations are properly tested with pytest-asyncio
