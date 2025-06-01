# Acorn Game Loader
A comprehensive GUI application for loading Acorn Electron and BBC Micro games onto original hardware with advanced tape control and save state functionality.

## Screenshot

![AGL](https://github.com/user-attachments/assets/eed01cdf-60b3-4b7e-85d8-f72748e27b3c)


## Features

### Core Functionality
- **Game Browser** with instant search (supports multi-term filtering)
- **Screenshot Viewer** (supports JPG, PNG, GIF)
- **Manual Viewer** (TXT format)
- Supports **.uef** game files
- **New in v1.2.0**: Edit Mode with game management tools

### Tape Control
- ▶️ **Play**: Start/Resume game playback
- ⏹️ **Stop**: Halt playback
- ⏏️ **Eject**: Completely end playback
- ⏪ **Rewind**: Move back 1 tape block
- ⏩ **Forward**: Jump to next tape block
- 🔢 **Block Counter**: Shows current playback position
- 0️⃣ **Counter Reset**: Mark reference point (e.g., after loading screens)
- ↪️ **Jump**: Jumps to block set by Counter Reset

### Save States
- 💾 **Save Game Progress**:
  - Records audio from Electron/BBC Micro's EAR port
  - Auto-detects signal start/stop
- 📂 **Load Game Progress**:
  - Browse and select saved .wav files
  - Simulates tape loading process
  - Status feedback during operation

### Convenience Features
- **Remember Last Game**: Auto-reopens your last-played game
- **Customizable Folders**: Set paths for games, images, manuals
- **New in v1.2.0**: Drag-and-drop support for adding games/images/manuals
- **New in v1.2.0**: Right-click context menu for game management
- **New in v1.2.0**: Updated in-app manual with Edit Mode documentation
- **New in v1.2.0**: About dialog with version/license info

## Requirements
- **Windows 10/11** (64-bit)
- **.NET Framework 8.0**
- **Python** (embedded in distribution)

## Installation
1. Download latest release
2. Extract to preferred location
3. Run `Acorn Game Loader.exe`
4. Optional - Download Assets.zip (Contains screenshots and game manuals/info rename your uef files to match)

## Usage Guide

### First-Time Setup
1. Open **Settings** (Menu → Settings)
2. Configure folders for:
   - Games (.uef files)
   - Images (screenshots as .jpg/.png/.gif)
   - Manuals (.txt files)
3. Enable "Remember Last Game" if desired

### Playing Games
1. Select game from list (use search to filter)
2. View screenshot and manual
3. Click **Play** to start or resume playback (after Rewind/Forward/Stop)
4. Use **Stop**, **Rewind**, **Forward** as needed

### Edit Mode Features (New in v1.2.0)
1. Enable **Edit Mode** (Menu → Edit → Editor On)
2. Select the game and right-click for options:
   - **Rename**: Change game name while keeping all associated files
   - **Move**: Relocate game to different folder
   - **Delete**: Remove game (sent to Recycle Bin)
3. Drag and drop files directly onto:
   - Game list (to add .uef files)
   - Image panel (to update screenshots)
   - Manual panel (to update documentation)

### Saving Progress
1. In-game, select or type the save command, it will thn say "Press Record Then Return" or something similar.
2. Click SAVE in the Game Saves section (button changes to STOP).
3. Wait for "Waiting for signal..." message.
4. Press RETURN on the Electron/BBC Micro and wait for save to finish.
5. Click STOP to end recording.
6. Application will automatically:
   - Detect the signal
   - Save as timestamped .wav file

### Loading Progress
1. In-game, select or type the load command.
2. Click LOAD in Game Saves and choose the desired .wav file.
3. File should begin loading on the Electron/BBC Micro.

## File Naming Convention
All supporting files must match game filename exactly:
- Game: `GameName.uef`
- Image: `GameName.jpg/png/gif`
- Manual: `GameName.txt`

## Technical Details
- Save system works with standard audio cables
- Optimized for 44.1kHz mono WAV files

## Troubleshooting
- **No sound during playback?** Check audio cable connections
- **Save/Load not working?** Ensure:
  - Adequate volume during save
  - Minimal background noise
  - Correct WAV format (44.1kHz mono)
- **Game missing from list?** Verify:
  - Correct folder location
  - Proper file extension (.uef)
  - File integrity
- **Edit Mode features not appearing?** Ensure:
  - Edit Mode is enabled (Menu → Edit → Editor On)
  - You're right-clicking on a game in the list

## Contributing
This project welcomes contributions under GPLv3 license. Feel free to:
- Report issues or suggest features
- Submit pull requests
- Fork for your own modifications

## License
GNU General Public License v3.0 - See [LICENSE](LICENSE) for details.
