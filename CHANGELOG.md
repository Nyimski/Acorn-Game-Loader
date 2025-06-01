# Changelog

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
