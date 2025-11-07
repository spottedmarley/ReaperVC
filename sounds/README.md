# Audio Prompts

This directory contains custom audio prompts for ReaperVC.

## Expected Files

Place your custom WAV files here:

- **`welcome.wav`** - Plays when the application starts (audio device test)
- **`action-complete.wav`** - Plays when a command completes successfully

## File Specifications

- **Format**: WAV (uncompressed PCM)
- **Sample Rate**: 44100 Hz recommended (but any rate works)
- **Channels**: Mono or Stereo (stereo will be converted to mono for JACK)
- **Bit Depth**: 16-bit recommended
- **Duration**: Keep short (< 1 second recommended for best UX)

## Fallback Behavior

If custom WAV files are not present, ReaperVC will use generated tones:
- **Welcome**: Single 880Hz beep (0.1s)
- **Action Complete**: Quick 1000Hz beep (0.1s)

## Creating Custom Sounds

You can create WAV files using any audio editor (Audacity, Reaper, etc.).

Example using `sox` command line:
```bash
# Generate a simple beep
sox -n welcome.wav synth 0.2 sine 880

# Generate action complete beep
sox -n action-complete.wav synth 0.1 sine 1000
```

## Volume

Audio volume is controlled by the `volume` setting in AudioFeedback (default: 0.3 = 30%).
Custom WAV files will have this volume multiplier applied automatically.
