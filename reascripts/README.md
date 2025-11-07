# ReaperVC ReaScripts

Control ReaperVC directly from within REAPER using these Lua scripts.

---

## Available Scripts

### 🎯 ReaperVC_Toggle.lua
**Start/stop ReaperVC**

- Checks if ReaperVC is running
- If stopped: starts it
- If running: stops it
- Most convenient for daily use

### 📊 ReaperVC_LaunchTelemetry.lua
**Open telemetry console**

- Launches live telemetry monitor in ReaScript console
- Shows speech recognition results, command matches, and execution status
- Can also be triggered by voice command: "open console"

### 📊 ReaperVC_HideTelemetry.lua
**Close telemetry console**

- Stops the telemetry monitor
- Can also be triggered by voice command: "close console"

### ⚙️ ReaperVC_SetPath.lua
**Configure installation path**

- Set the path to your ReaperVC installation
- Necessary if installed in non-default location
- Saves setting permanently

---

## Installation

### Step 1: Load Required Scripts in REAPER

**Required for voice commands to work:**

1. Open REAPER
2. Go to **Actions → Show action list**
3. Click **New action → Load ReaScript...**
4. Navigate to: `/path/to/ReaperVC/reascripts/`
5. Load these scripts:
	- `ReaperVC_LaunchTelemetry.lua` (required for "open console" command)
	- `ReaperVC_HideTelemetry.lua` (required for "close console" command)

**Optional (for manual control):**
	- `ReaperVC_Toggle.lua` (start/stop from REAPER)
	- `ReaperVC_SetPath.lua` (if using non-default install location)

### Step 2: Generate Actions List

After loading the required scripts:

1. In Actions list, search for: `SWS/S&M: Dump action list`
2. Run this action
3. Save output to: `ReaperVC/reaper-actions.txt`

This maps action names to IDs for your installation.

### Step 3: Configure Path (if needed)

If ReaperVC is NOT installed at `~/Apps/Audio/ReaperVC`:

1. Run the action: **Script: ReaperVC_SetPath.lua**
2. Enter your installation path
3. Click OK

The path is saved permanently in REAPER's settings.

### Step 4: Assign Shortcuts (optional)

Make it even more convenient:

1. In Actions list, find `Script: ReaperVC_Toggle.lua`
2. Right-click → Add shortcut
3. Assign a key (e.g., `Ctrl+Shift+V`)

Now you can start/stop ReaperVC with a keyboard shortcut!

---

## Usage

### Starting ReaperVC

**From REAPER:**
- Run action: `Script: ReaperVC_Toggle.lua`
- Or use your assigned keyboard shortcut

**From terminal:**
```bash
cd /path/to/ReaperVC
./reaper-vc.sh
```

### Using Voice Commands

Once ReaperVC is running:
- Say "play" to start playback
- Say "record" to start recording
- Say "stop" to stop
- Say "open console" to view live telemetry
- Say "close console" to hide telemetry
- Say "stop listening" to shutdown ReaperVC

See `config/default_commands.yaml` for all available commands.

### Monitor Live Telemetry

Say "open console" or run `Script: ReaperVC_LaunchTelemetry.lua` to see real-time activity:
- Speech recognition results
- Command matches and confidence scores
- Action execution status
- System events

The telemetry monitor displays all ReaperVC activity in the ReaScript console as it happens. This is especially useful for:
- Debugging command recognition issues
- Monitoring confidence scores
- Understanding why a command didn't work
- Testing new custom commands

**Tip**: Keep the telemetry monitor running during recording sessions!

### Stopping ReaperVC

- Say "stop listening"
- Or run: `Script: ReaperVC_Toggle.lua` (when already running)

---

## Troubleshooting

**ReaperVC won't start**
- Check `/tmp/reapervc.log` for errors
- Make sure Python dependencies are installed
- Try running `./reaper-vc.sh` manually first
- Verify REAPER OSC is configured (see main README)

**Voice commands not recognized**
- Check microphone input in `config/voice_config.yaml`
- Test microphone: `python3 -m sounddevice`
- Adjust VAD sensitivity settings
- Enable telemetry console to monitor recognition

**"Open console" command doesn't work**
- Make sure `ReaperVC_LaunchTelemetry.lua` is loaded in Actions
- Regenerate `reaper-actions.txt` (see Step 2 above)
- Check `/tmp/reapervc.log` for error messages

---

## Integration Tips

### Auto-start with REAPER

Want ReaperVC to start automatically when REAPER opens?

1. Actions → Show action list
2. Find `Script: ReaperVC_Toggle.lua`
3. Right-click → Copy selected action command ID
4. File → Project settings → Run action on project open
5. Paste the command ID

### Keyboard Shortcuts

Suggested shortcuts:
- `Ctrl+Shift+V` - Toggle ReaperVC
- `Ctrl+Shift+C` - Open telemetry console

### Toolbar Button

Add ReaperVC to your toolbar:

1. Right-click REAPER toolbar → Customize toolbar
2. Click **Add...**
3. Find `Script: ReaperVC_Toggle.lua`
4. Adjust icon/text as desired
5. Click OK

---

## How It Works

### Process Management

The scripts use standard Linux process management:

- **Start**: Runs `./reaper-vc.sh` in background using `nohup`
- **Stop**: Sends voice command "stop listening" or kills process
- **Toggle**: Checks running status and starts/stops accordingly

### Logging

All ReaperVC output goes to `/tmp/reapervc.log`

View live log:
```bash
tail -f /tmp/reapervc.log
```

### Path Configuration

The installation path is stored in REAPER's ExtState:
- Section: `"ReaperVC"`
- Key: `"install_path"`
- Persists across REAPER sessions

---

## Compatibility

### Operating Systems

- ✅ **Linux** - Fully supported
- ✅ **macOS** - Should work (minor path adjustments may be needed)
- ⚠️ **Windows** - Requires WSL or different process management

### REAPER Versions

- Tested on REAPER 6.x and 7.x
- Requires Lua scripting support (built-in)
- Requires SWS Extensions for action list export

---

## Support

**Having issues?**

1. Check `/tmp/reapervc.log` for errors
2. Verify installation path is correct
3. Make sure OSC is configured in REAPER
4. Test manually: `./reaper-vc.sh`
5. Open an issue on GitHub with log output

**Feature requests?**

Open a GitHub issue or discussion!

---

**Happy voice-controlled recording!** 🎙️
