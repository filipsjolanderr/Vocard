import json
import os
from pathlib import Path

# Define the categorization mapping
CATEGORY_MAPPING = {
    # Common
    "enabled": "common.status.enabled",
    "disabled": "common.status.disabled",
    "live": "common.status.live",
    "unknownException": "common.errors.unknown",
    "missingIntents": "common.errors.missingIntents",
    # "decodeError": "common.errors.decodeError",
    
    # Voice
    "connect": "voice.connection.connect",
    "noChannel": "voice.connection.noChannel",
    "alreadyConnected": "voice.connection.alreadyConnected",
    "noPermission": "voice.connection.noPermission",
    "notInChannel": "voice.connection.notInChannel",
    # "noVoiceChannel": "voice.connection.noVoiceChannel",
    "setStageAnnounceTemplate": "voice.stageChannel.setAnnounceTemplate",
    
    # Player errors
    "nodeReconnect": "player.errors.nodeReconnect",
    "noPlayer": "player.errors.noPlayer",
    "noPlaySource": "player.errors.noPlaySource",
    "noTrackPlaying": "player.errors.noTrackPlaying",
    "noTrackFound": "player.errors.noTrackFound",
    # "missingTrackInfo": "player.errors.missingTrackInfo",
    
    # Player playback
    "trackLoad": "player.playback.trackLoad",
    "trackLoad_pos": "player.playback.trackLoadPos",
    "playlistLoad": "player.playback.playlistLoad",
    "nowplayingDesc": "player.playback.nowplayingDesc",
    "nowplayingField": "player.playback.nowplayingField",
    "nowplayingLink": "player.playback.nowplayingLink",
    
    # Player controls - pause
    "pauseError": "player.controls.pause.error",
    "pauseVote": "player.controls.pause.vote",
    "paused": "player.controls.pause.success",
    
    # Player controls - resume
    "resumeError": "player.controls.resume.error",
    "resumeVote": "player.controls.resume.vote",
    "resumed": "player.controls.resume.success",
    
    # Player controls - skip
    "skipError": "player.controls.skip.error",
    "skipVote": "player.controls.skip.vote",
    "skipped": "player.controls.skip.success",
    
    # Player controls - back
    "backVote": "player.controls.back.vote",
    "backed": "player.controls.back.success",
    
    # Player controls - leave
    "leaveVote": "player.controls.leave.vote",
    "left": "player.controls.leave.success",
    
    # Player controls - shuffle
    "shuffleError": "player.controls.shuffle.error",
    "shuffleVote": "player.controls.shuffle.vote",
    "shuffled": "player.controls.shuffle.success",
    
    # Player controls - other
    "seek": "player.controls.seek",
    "forward": "player.controls.forward",
    "rewind": "player.controls.rewind",
    "replay": "player.controls.replay",
    "repeat": "player.controls.repeat",
    "autoplay": "player.controls.autoplay",
    
    # Player buttons
    "buttonBack": "player.buttons.back",
    "buttonPause": "player.buttons.pause",
    "buttonResume": "player.buttons.resume",
    "buttonSkip": "player.buttons.skip",
    "buttonLeave": "player.buttons.leave",
    "buttonLoop": "player.buttons.loop",
    "buttonVolumeUp": "player.buttons.volumeUp",
    "buttonVolumeDown": "player.buttons.volumeDown",
    "buttonVolumeMute": "player.buttons.volumeMute",
    "buttonVolumeUnmute": "player.buttons.volumeUnmute",
    "buttonAutoPlay": "player.buttons.autoPlay",
    "buttonShuffle": "player.buttons.shuffle",
    "buttonForward": "player.buttons.forward",
    "buttonRewind": "player.buttons.rewind",
    "buttonLyrics": "player.buttons.lyrics",
    
    # Player dropdown
    "playerDropdown": "player.dropdown.trackSelect",
    # "playerFilter": "player.dropdown.filterSelect",
    
    # Queue management
    "queueTitle": "queue.management.title",
    "cleared": "queue.management.cleared",
    "removed": "queue.management.removed",
    "swapped": "queue.management.swapped",
    "moved": "queue.management.moved",
    
    # Queue view
    "viewTitle": "queue.view.title",
    "viewDesc": "queue.view.desc",
    "historyTitle": "queue.view.historyTitle",
    
    # Queue errors
    "voicelinkQueueFull": "queue.errors.queueFull",
    "voicelinkOutofList": "queue.errors.outOfList",
    "voicelinkDuplicateTrack": "queue.errors.duplicateTrack",
    
    # Search
    "searchTitle": "search.title",
    "searchDesc": "search.desc",
    "searchWait": "search.wait",
    # "searchTimeout": "search.timeout",
    "searchSuccess": "search.success",
    "noLinkSupport": "search.noLinkSupport",
    
    # Playlist view
    "playlistViewTitle": "playlist.view.title",
    "playlistViewHeaders": "playlist.view.headers",
    "playlistFooter": "playlist.view.footer",
    "playlistView": "playlist.view.detailTitle",
    "playlistViewDesc": "playlist.view.detailDesc",
    "playlistViewPermsValue": "playlist.view.permsValue",
    "playlistViewPermsValue2": "playlist.view.permsValue2",
    "playlistViewTrack": "playlist.view.trackList",
    "playlistViewFooter": "playlist.view.footer2",
    # "playlistViewPage": "playlist.view.page",
    
    # Playlist actions
    "playlistPlay": "playlist.actions.play",
    "playlistCreated": "playlist.actions.created",
    "playlistRenamed": "playlist.actions.renamed",
    "playlistRemove": "playlist.actions.removed",
    "playlistRemoved": "playlist.actions.trackRemoved",
    "playlistClear": "playlist.actions.cleared",
    "playlistAdded": "playlist.actions.trackAdded",
    
    # Playlist errors
    "playlistNotFound": "playlist.errors.notFound",
    "playlistNotAccess": "playlist.errors.noAccess",
    "playlistNoTrack": "playlist.errors.noTrack",
    "playlistNotAllow": "playlist.errors.notAllowed",
    "playlistOverText": "playlist.errors.nameOverLimit",
    "playlistSameName": "playlist.errors.sameName",
    "playlistDeleteError": "playlist.errors.deleteDefault",
    "playlistPositionNotFound": "playlist.errors.positionNotFound",
    "playlistNotInvalidUrl": "playlist.errors.invalidUrl",
    "playlistExists": "playlist.errors.exists",
    "overPlaylistCreation": "playlist.errors.limitReached",
    "playlistLimitTrack": "playlist.errors.trackLimitReached",
    "playlistPlaylistLink": "playlist.errors.playlistLinkNotAllowed",
    "playlistStream": "playlist.errors.streamNotAllowed",
    "playlistAddError": "playlist.errors.streaming",
    "playlistAddError2": "playlist.errors.track",
    "playlistLimited": "playlist.errors.trackLimited",
    "playlistRepeated": "playlist.errors.trackRepeated",
    # "emptyPlaylistMessage": "playlist.errors.emptyPlaylist",
    
    # Playlist sharing
    "playlistSendErrorPlayer": "playlist.sharing.sendErrorPlayer",
    "playlistSendErrorBot": "playlist.sharing.sendErrorBot",
    "playlistBelongs": "playlist.sharing.belongs",
    "playlistShare": "playlist.sharing.alreadyShared",
    "playlistSent": "playlist.sharing.alreadySent",
    "noPlaylistAcc": "playlist.sharing.noAccount",
    "invitationSent": "playlist.sharing.invitationSent",
    
    # Playlist inbox
    "inboxFull": "playlist.inbox.full",
    "inboxNoMsg": "playlist.inbox.noMessages",
    
    # Effects
    "addEffect": "effects.added",
    "clearEffect": "effects.cleared",
    "filterTagAlreadyInUse": "effects.tagInUse",
    
    # Lyrics
    "lyricsNotFound": "lyrics.notFound",
    
    # Settings menu
    "settingsMenu": "settings.menu",
    "settingsTitle": "settings.basic.title",
    "settingsValue": "settings.basic.value",
    "settingsTitle2": "settings.queue.title",
    "settingsValue2": "settings.queue.value",
    "settingsTitle3": "settings.voice.title",
    "settingsPermTitle": "settings.permissions.title",
    "settingsPermValue": "settings.permissions.value",
    
    # Settings actions
    "languageNotFound": "settings.actions.languageNotFound",
    "changedLanguage": "settings.actions.languageChanged",
    "setPrefix": "settings.actions.prefixSet",
    "setDJ": "settings.actions.djSet",
    "setQueue": "settings.actions.queueModeSet",
    "247": "settings.actions.mode247",
    "bypassVote": "settings.actions.bypassVote",
    "setVolume": "settings.actions.volumeSet",
    "toggleController": "settings.actions.controllerToggled",
    "toggleDuplicateTrack": "settings.actions.duplicateTrackToggled",
    "toggleControllerMsg": "settings.actions.controllerMsgToggled",
    "toggleSilentMsg": "settings.actions.silentMsgToggled",
    
    # Permissions
    "notdj": "permissions.notDj",
    "djToMe": "permissions.djToSelf",
    "djNotInChannel": "permissions.djNotInChannel",
    "djswap": "permissions.djSwapped",
    "missingPosPerm": "permissions.missingPosition",
    "missingModePerm": "permissions.missingMode",
    "missingQueuePerm": "permissions.missingQueue",
    "missingAutoPlayPerm": "permissions.missingAutoPlay",
    "missingFunctionPerm": "permissions.missingFunction",
    "noCreatePermission": "permissions.noCreatePermission",
    
    # Voting
    # "notVote": "voting.notVoted",
    "voted": "voting.voted",
    
    # Ping
    "pingTitle1": "ping.title1",
    "pingTitle2": "ping.title2",
    "pingField1": "ping.field1",
    "pingField2": "ping.field2",
    
    # Song Request
    "createSongRequestChannel": "songRequest.channelCreated",
    
    # Time
    "timeFormatError": "time.formatError",
    "invalidStartTime": "time.invalidStartTime",
    "invalidEndTime": "time.invalidEndTime",
    # "invalidTimeOrder": "time.invalidTimeOrder",
}


def unflatten_json(flat_json, separator='.'):
    """Convert a flattened JSON object back to nested structure."""
    nested = {}
    
    for key, value in flat_json.items():
        keys = key.split(separator)
        current = nested
        
        for i, k in enumerate(keys[:-1]):
            if k not in current:
                current[k] = {}
            current = current[k]
        
        current[keys[-1]] = value
    
    return nested


def categorize_language_json(input_data, mapping=CATEGORY_MAPPING):
    """
    Categorize a flat language JSON using the mapping.
    
    Args:
        input_data (dict): The flat language JSON
        mapping (dict): The categorization mapping
    
    Returns:
        dict: Categorized nested JSON
    """
    categorized_flat = {}
    unmapped_keys = []
    
    for old_key, value in input_data.items():
        if old_key in mapping:
            new_key = mapping[old_key]
            categorized_flat[new_key] = value
        else:
            unmapped_keys.append(old_key)
            # Keep unmapped keys in a special category
            categorized_flat[f"unmapped.{old_key}"] = value
    
    if unmapped_keys:
        print(f"⚠️  Warning: {len(unmapped_keys)} unmapped keys found:")
        for key in unmapped_keys[:10]:  # Show first 10
            print(f"   - {key}")
        if len(unmapped_keys) > 10:
            print(f"   ... and {len(unmapped_keys) - 10} more")
    
    return unflatten_json(categorized_flat)


def process_language_file(input_file, output_file):
    """
    Process a single language file and categorize it.
    
    Args:
        input_file (str): Path to input JSON file
        output_file (str): Path to output JSON file
    """
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        categorized = categorize_language_json(data)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(categorized, f, ensure_ascii=False, indent=4)
        
        print(f"✓ Successfully processed: {input_file} -> {output_file}")
        
    except FileNotFoundError:
        print(f"✗ Error: File '{input_file}' not found")
    except json.JSONDecodeError:
        print(f"✗ Error: Invalid JSON in file '{input_file}'")
    except Exception as e:
        print(f"✗ Error processing {input_file}: {str(e)}")


def batch_process_languages(input_dir, output_dir, pattern="*.json"):
    """
    Process all language JSON files in a directory.
    
    Args:
        input_dir (str): Directory containing input JSON files
        output_dir (str): Directory to save categorized JSON files
        pattern (str): File pattern to match (default: "*.json")
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    
    # Create output directory if it doesn't exist
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Find all matching files
    files = list(input_path.glob(pattern))
    
    if not files:
        print(f"No files found matching pattern '{pattern}' in '{input_dir}'")
        return
    
    print(f"Found {len(files)} file(s) to process\n")
    
    success_count = 0
    for file in files:
        output_file = output_path / file.name
        try:
            process_language_file(str(file), str(output_file))
            success_count += 1
        except Exception as e:
            print(f"✗ Failed to process {file.name}: {str(e)}")
    
    print(f"\n{'='*50}")
    print(f"Processing complete: {success_count}/{len(files)} files successfully processed")


# Example usage
if __name__ == "__main__":
    print("Language JSON Categorizer")
    print("="*50)
    
    code = "ZHCN"
    input_file = f'langs/{code}.json'
    output_file = f'langs/{code}.json'
    process_language_file(f'{input_file}', f'{output_file}')