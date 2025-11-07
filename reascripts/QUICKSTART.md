# ReaperVC ReaScripts - Quick Start

Control ReaperVC from inside REAPER with these Lua scripts!

---

## 🚀 30-Second Setup

### Load the Toggle Script (Easiest)

1. Open REAPER
2. **Actions → Show action list**
3. **New action → Load ReaScript...**
4. Navigate to: `ReaperVC/reascripts/ReaperVC_Toggle.lua`
5. Click OK

**Done!** Now you can run "Script: ReaperVC_Toggle.lua" from the Actions list.

---

## 🎯 Usage

### Start ReaperVC

1. Run action: **Script: ReaperVC_Toggle.lua**
2. Click "Yes" to start
3. Wait 2 seconds for initialization
4. Start speaking commands!

### Stop ReaperVC

1. Run action: **Script: ReaperVC_Toggle.lua**
2. Click "Yes" to stop

---

## ⌨️ Add Keyboard Shortcut (Recommended)

1. In Actions list, find **Script: ReaperVC_Toggle.lua**
2. Right-click → **Add shortcut**
3. Press: `Ctrl+Shift+V` (or your preference)
4. Click OK

Now just press `Ctrl+Shift+V` to toggle ReaperVC on/off!

---

## 🔧 If Installed in Custom Location

If ReaperVC is NOT at `~/Apps/Audio/ReaperVC`:

1. Load: `ReaperVC_SetPath.lua`
2. Run it once
3. Enter your installation path
4. Click OK

Path is saved permanently.

---

## 📋 All Available Scripts

| Script | Purpose |
|--------|---------|
| **ReaperVC_Toggle.lua** | Start/stop ReaperVC |
| ReaperVC_LaunchTelemetry.lua | Open telemetry console |
| ReaperVC_HideTelemetry.lua | Close telemetry console |
| ReaperVC_SetPath.lua | Set installation path |

---

## 🐛 Troubleshooting

**"ReaperVC is currently running" but you didn't start it**
- Stale process from previous session
- Solution: Run **`ReaperVC_CleanupAndStart.lua`**
- This kills old processes and starts fresh

**"Failed to stop ReaperVC"**
- Run **`ReaperVC_CleanupAndStart.lua`** to force cleanup

**"ReaperVC not found"**
- Run `ReaperVC_SetPath.lua` and set correct path

**Won't start**
- Check `/tmp/reapervc.log` for errors
- Make sure Python dependencies installed
- Try running `./reaper-vc.sh` manually first

**Check status**
- Run `ReaperVC_Status.lua` to see what's happening

---

## 📖 Full Documentation

See [README.md](README.md) for complete documentation.

---

**That's it! Happy voice-controlled recording!** 🎙️
