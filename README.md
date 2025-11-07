# ReaperVC - Voice Control for REAPER DAW

**Powerful and highly configurable voice control for Reaper**

---

## Usage example

You're a solo producer. Maybe it's just you, your guitar and Reaper alone in your bedroom studio and you want to record yourself playing.
You stand up with your guitar strapped on, pick in hand, head phones on and ready to record some sweet riffs. Wouldn't it be nice if you
could...

- Start/stop recording
- Instantly reject/delete bad takes and begin fresh ones
- Save your project
- Rewind, loop, pause, play... anything!
- Trigger all your powerful custom actions

...all without lifting a finger from your instrument?

ReaperVC to the rescue!

## The Solution

ReaperVC comes with many default voice commands already pre-mapped so that
common phrases are mapped to common reaper actions. The default mappings are
generally useful for the 'solo producer' use case mentioned above: common
commands for hands-free recording. Here is an example of how the default
voice commands can be used in that work flow.

```
You: "add a new track"
    [A new track is added to track list]

You: "record arm"
    [Track arms for recording]

You: "record"
    [Recording starts]
    [You play guitar]

You: "stop"
    [Recording stops]

You: "set tempo to 120"
    [Tempo is set to 120BPM]

You: "turn on the metronome"
    [Metronome toggles: ON]

You: "Ok... let's try again"
    [Last take is deleted, recording starts again]
    [You play guitar]

You: "stop"
    [Recording stops]

You: "turn off the metronome"
    [Metronome toggles: OFF]

You: "playback"
    [Playback starts]

You: "stop"
    [Playback stops]

You: "Perfect! Keep that one."
    [Track disarms, ready for next part]

You: "save project"
    [Project is saved]


```

**No keyboard. No mouse. Just your voice.**

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Up Reaper

1. Install [SWS Extension](https://www.sws-extension.org/)
2. Enable OSC: Options → Preferences → Control/OSC/web
3. Load ReaperVC LUA scripts:
    ReaperVC includes Lua scripts used to toggle ReaperVC on/off and to toggle display of the voice telemetry (debugging) console:
    In Reaper...
    1. Press '?' to open the actions list
    2. Bottom right, click 'New Action' > 'Load ReaScript'
    3. Load these scripts one by one from 'reascripts/' directory:
        - ReaperVC_SetPath.lua - Sets the root folder where ReaperVC is running from
        - ReaperVC_Toggle.lua - Starts/stops ReaperVC
        - ReaperVC_LaunchTelemetry.lua - Opens telemetry console (for "open console" voice command)
        - ReaperVC_HideTelemetry.lua - Closes telemetry console (for "close console" voice command)

    See [reascripts/README.md](reascripts/README.md) for details.

    (Optional) Create a keyboard shortcut to start/stop ReaperVC
        - In action list, find and right-click: 'Script: ReaperVC_Toggle.lua'
        - Choose 'Add keyboard shortcut for action'
        - (I like ctrl+shift+v ... but you do you)
4. Run: ReaperVC_SetPath.lua script to set the location folder
5. Run: SWS/S&M: Dump action list (all actions)
6. Save output as reaper-actions.txt in the root ReaperVC folder

### 3. Start Using Voice Commands

Start ReaperVC by executing ReaperVC_Toggle.lua (or use a keyboard shortcut)

If ReaperVC is properly configured, after a moment you will hear a welcome prompt:
'ReaperVC is listening. Speak a command.'

Speak naturally:
- **"new track"** - New track added to track list
- **"record"** - Start recording
- **"stop"** - Stop recording
- **"try again"** - Delete last take and re-record
- **"keep this take"** - Disarm track (confirm the take)
- **"save"** - Save project

**That's it!** Simple commands that just work.

### List of default voice commands

In the /config folder of ReaperVC there are two files:

**default_commands.yaml** - Common commands that trigger standard (stock) Reaper actions. These work in everyone's Reaper DAW right out of the box.

**custom_commands.yaml** - Contains example commands demonstrating advanced features (text input, key pressing, delays). Use these as templates for your own custom commands. Commands here override matching commands in default_commands.yaml.

### Real-time Voice Processing Telemetry Console

Watch in real-time what the system is doing:
(Voice command: 'Open console')

```
[12:06:54] [Heard   ] [OK] 'New track.' (conf=0.99)
[12:06:54] [Spoken  ] Received: 'New track.'
[12:06:54] [Command ] Matched: new_track (confidence: 1.00)
[12:06:54] [Reaper  ] [→] Sending action _f902a3e7d232fc3b1471ea881c28613a: Add a new track, edit track name
[12:06:54] [Keyboard] Typing: New Track
[12:06:54] [Keyboard] [OK] Typed: New Track
[12:06:54] [Keyboard] Pressing key: Return
[12:06:54] [Keyboard] [OK] Pressed: Return
[12:06:54] [Reaper  ] [OK] Add a new track, edit track name
[12:06:55] [Result  ] Success: new_track
[12:07:01] [Heard   ] [OK] 'arm toggle.' (conf=0.96)
[12:07:01] [Spoken  ] Received: 'arm toggle.'
[12:07:01] [Command ] Matched: arm_track (confidence: 1.00)
[12:07:01] [Reaper  ] [→] Sending action 817: Toggle record arm for last touched track
[12:07:01] [Reaper  ] [OK] Toggle record arm for last touched track
[12:07:01] [Result  ] Success: arm_track
[12:07:08] [Heard   ] [?] 'you' (conf=0.10) - Low confidence
[12:07:08] [Heard   ] Filtered: Confidence too low (0.10), ignoring
[12:07:12] [Heard   ] [OK] 'Start recording.' (conf=0.99)
[12:07:12] [Spoken  ] Received: 'Start recording.'
[12:07:12] [Command ] Matched: record (confidence: 1.00)
[12:07:12] [State   ] Playback state: Recording
[12:07:12] [Reaper  ] [→] Sending action 1013: Start recording
[12:07:12] [Reaper  ] [OK] Start recording
[12:07:13] [Result  ] Success: record
[12:07:17] [Heard   ] [OK] 'Stop.' (conf=0.99)
[12:07:17] [Spoken  ] Received: 'Stop.'
```

**Telemetry console is incredibly useful for:**
- Understanding what the system hears
- Debugging custom commands
- Learning which phrases work best for your voice
- Seeing exactly what went wrong when a command fails

### Command List Window

Use the voice command, 'command list' to open a seperate window that contains a list of every valid speech pattern being listened for by ReaperVC, including all custom commands that you may have added. This is a valuable resource to have while you are learning the voice commands that are available to you, especially if you've added many of your own commands and have trouble remembering some of them. If you have dual monitors, try maximizing the command list window on your second monitor to have a quick visual reference to check while you're editing/recording on your main monitor. The command list is visually configurable with regard to font size (+/- buttons) and command groupings (click the [x] button on a group of commands to remove that group from the window, making room for other groups or larger font selection.)

### 🛠️ Easy Customization

Add your own commands in minutes! Edit config/default_commands.yaml or create config/custom_commands.yaml:

```yaml
your_command:
  group: "Group name"
  patterns:
    - "your phrase here"
    - "alternative phrase"
  action_name: "File: Render project"
  description: "What this does"
  available_during_recording: false
```

See [Adding Custom Commands](docs/ADDING_COMMANDS.md) for detailed guide with examples.

### 📊 Detailed Session Logs

Every session saves a complete telemetry log to extras/telemetry.md:

- All speech transcriptions with confidence scores
- All commands matched/unrecognized
- All actions executed with timestamps
- Complete chronological timeline
- Perfect for debugging and sharing issues

### Key Technologies

- **Whisper** - OpenAI's speech-to-text (runs locally, no API)
- **WebRTC VAD** - Voice activity detection (knows when you've stopped speaking)
- **OSC** - Open Sound Control (communicates with REAPER)
- **Action Name Mapping** - Makes configs portable across REAPER installations

## Requirements

### Hardware
- **Microphone** (any USB mic works)
- **Headphones** (REQUIRED for playback monitoring - see below)

### Software
- **Python 3.8+**
- **REAPER** with OSC enabled
- **SWS Extension** (provides essential actions)

### Audio Backend
**Works with ALSA, PulseAudio, JACK**

ReaperVC automatically detects and uses whatever audio system you have:
- **ALSA** - Direct hardware access (works out of the box)
- **PulseAudio** - Most common on modern Linux desktops
- **JACK** - Auto-detected if running (optional, not required)

### Important: Use Headphones!

Why? When playback comes through speakers, your microphone picks it up. This can confuse the Voice Activity Detection (can't tell when you've stopped speaking). Result: commands get buffered and only execute when playback stops.

**With headphones:** Commands work instantly during playback ✅
**Without headphones:** Commands delayed/batched ❌

## Documentation
🛠️ **[Adding Custom Commands](docs/ADDING_COMMANDS.md)** - Step-by-step guide with telemetry examples

## Contributing

Want to improve ReaperVC? Awesome!

### Easy Contributions
- Report bugs (include `extras/telemetry.md`)
- Suggest new built-in commands
- Improve documentation
- Share your custom commands

### Code Contributions
- Keep it simple (remember: 250 lines)
- Focus on recording workflow
- No AI complexity
- Include tests

## Credits

### Technologies
- [OpenAI Whisper](https://github.com/openai/whisper) - Speech recognition
- [WebRTC VAD](https://github.com/wiseman/py-webrtcvad) - Voice activity detection
- [python-osc](https://github.com/attwad/python-osc) - REAPER communication
- [SWS Extension](https://www.sws-extension.org/) - Essential REAPER actions

## License

MIT License - Use it, modify it, share it!

## Support

**Found a bug?** Open an issue with your `extras/telemetry.md` file.

**Have a question?** Check the [docs](docs/) first, then open an issue.

**Want to share a cool custom command?** Open a discussion!

###### ReaperVC #####

**Simple useful commands for when you can't use your hands.**

(Hey, that rhymes!)

🎙️ **Happy recording!**