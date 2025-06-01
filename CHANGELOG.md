# Changelog

## v1.2.1 - 2025-06-01

### Bug Fixes
- Resolved issue where the UI did not return to the last selected game in v1.2.0.

### Improved

- Removed DeleteTempFiles.bat; temporary file cleanup is now handled directly by Form1.vb.
- 
## v1.2.0 - 2025-06-01

### Added
- Comprehensive Edit Mode system with toggle
- Context menu for game management (rename/move/delete)
- Drag-and-drop support for games/images/manuals
- About dialog with version/license/contact info
- Updated in-app manual

### Improved
- File operation safety and error handling
- Resource management
- Process handling

## [v1.1.0] - 2025-05-22

### Control Scheme Changes
- **Revised playback controls** to better match original hardware behavior:
  - ⏹️ **Stop** now pauses playback
  - ▶️ **Play** handles resume
  - ⏏️ **Eject** terminates playback completely (replaces old Stop behavior)

### New Features
- ↪️ Added **Jump** functionality
- 🔄 Auto-scroll for game names exceeding 78 characters
- ⚡ Auto-pause during Fast Forward/Rewind operations

### UI Improvements
- Removed dedicated Pause/Resume button (streamlined into Stop/Play)
- Renamed "Set 000" to clearer "Counter Reset" label
- Updated all control descriptions and tooltips

### Technical Improvements
- Namespace standardized to `Acorn_Game_Loader`
- `UEFPLAY.PY` timing precision improved (0x0116 exact values fix cumulative drift)
