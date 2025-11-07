# Adding Custom Commands to ReaperVC

**Creating your own voice commands is straightforward!** This guide shows you how to add commands and use the built-in telemetry to test and debug them.

## Quick Overview

Adding a custom command involves 3 simple steps:

1. **Find the action** in reaper-actions.txt
2. **Add it** to config/custom_commands.yaml
3. **Test it** using the live telemetry in your terminal

### The Command Pipeline

When you speak, your command goes through this pipeline:

```
Your Voice → STT (Speech-to-Text) → Pattern Matching → Action Execution
```

### Example: Successful Command

```
[OK] 'stop' (conf=0.97)
[Voice] 'stop'
[Match] stop (confidence: 1.00)
[Transport State] Stopped
[→] Stop playback/recording
[OK] Stop playback/recording
```

### Example: Command Not Found

```
[OK] 'mixer' (conf=0.94)
[Voice] 'mixer'
[?] Unrecognized command: 'mixer'
```

**This is your signal to add the command!**

## Step-by-Step: Adding Your First Command

Let's add a "mixer" command that toggles the mixer open/closed.

### Step 1: Test Your Voice First

Before adding the command, run ReaperVC and say your phrase out loud. Watch the telemetry:

1. Start ReaperVC
2. Say 'Open console' (Telemetry console opens)
3. Say 'mixer'

You should see:
```
[OK] 'mixer' (conf=0.95)
[Voice] 'mixer'
[?] Unrecognized command: 'mixer'
```

**This confirms:**
- ✅ STT heard you correctly ("mixer")
- ✅ Confidence is high (0.95)
- ✅ Pattern doesn't exist yet (unrecognized)

### Step 2: Find the Reaper Action

In Reaper...
1. Press '?' to open the action list
2. Find the action called "View: Toggle mixer visible"
3. Right-click on it and choose "Copy selected action text"

### Step 3: Add it to your custom commands

Open config/custom_commands.yaml and add your command:

```yaml
  toggle_mixer:
    group: "My Custom Commands"
    patterns:
      - "mixer"
    action_name: "View: Toggle mixer visible"
    description: "Toggle mixing console"    
    available_during_recording: false
```

**Configuration breakdown:**

- **toggle_mixer:** - ReaperVC's param name for this command (use lowercase with underscores)
- **group:** - Command belongs to this group. When you open the command list window (voice prompt:'command list') all commands are organized into groups.
- **patterns:** - List of phrases that trigger this command
  - Can have multiple alternatives
  - Use lowercase (system normalizes input)
  - More specific patterns win (see "Pattern Matching" section below)
- **action_name:** - Exact action name (copied from reaper actions list)
  - Must match EXACTLY (case-sensitive)
  - System will resolve this to the action ID at startup
- **description:** - What this command does (shown in telemetry)
- **available_during_recording:** - Can this run while recording?
  - false - Command disabled during recording (safer)
  - true - Command works anytime

### Step 4: Restart ReaperVC

1. If ReaperVC is running, say 'stop listening' to kill it.
2. Start ReaperVC
3. Watch the startup output for your command:

```
[+] Initializing ReaperVC Transport Mode...
  mixer: View: Toggle mixer visible → 40078
```

**If you see an error:**
```
[ERROR] mixer: Action 'View: Toggle mixer visible' not found in reaper-actions.txt
```

This means the action name was not found in reaper-actions.txt. Action text spelling/punctuation may be wrong.

### Step 5: Test Your Command

1. Start ReaperVC
2. Say: 'open console' (voice telemetry console opens)
3. Say: 'mixer'

Watch the telemetry:

```
[OK] 'mixer' (conf=0.94)
[Voice] 'mixer'
[Match] toggle_mixer (confidence: 1.00)
[→] Toggle mixing console
[OK] Toggle mixing console
```

**Success!** Your command is working!

**Verify in Reaper:**
- The mixer should have toggled open/closed
- Try saying it again to toggle back

## Advanced: Multiple Actions in Sequence

Some commands need multiple actions to run in sequence (like "new track" which creates a track AND arms it).

**Example: Create a "solo mode" command**

This command will:
1. Mute all tracks
2. Select track 1
3. Unmute track 1

```yaml
  solo_mode:
    group: "Track List"
    patterns:
      - "solo mode"
      - "solo track one"
    action_names:
      - "Track: Mute/unmute all tracks"
      - "Track: Select track 01"
      - "Track: Toggle mute for track 01"
    description: "Solo track 1 (mute all others)"
    available_during_recording: false
```

**Key difference:** Use 'action_names:' (plural) instead of 'action_name:' (singular) for multiple actions.

Actions execute in order with a 100ms delay between each.

## Pattern Matching Tips

### How Patterns Work

The system uses **substring matching** with **longest pattern preference**.

**Example:**

If you have:
```yaml
record:
  patterns:
    - "record"

arm_track:
  patterns:
    - "record arm"
```

When you say **"record arm"**:
- "record" matches (6 characters)
- "record arm" matches (10 characters)
- System chooses "record arm" ✅ (longer = more specific)

### Best Practices

**✅ DO:**
- Use multiple pattern variations: `["undo", "undo that", "undo last"]`
- Keep patterns lowercase (system normalizes)
- Test with your actual voice (accents matter!)
- Check telemetry to see what STT actually hears

**❌ DON'T:**
- Use very short patterns alone ("go", "do") - too generic
- Rely on punctuation (it's stripped)
- Use numbers/special characters (alphanumeric only)

### Testing Pattern Conflicts

If two commands have overlapping patterns, watch the telemetry:

Say: **"start"**

```
[OK] 'start' (conf=0.96)
[Voice] 'start'
[Match] play (confidence: 0.80)  ← Partial match, check if this is correct!
```

If the wrong command triggers, make your patterns more specific:
- Change `"start"` to `"start playback"`
- Change `"record"` to `"start recording"`

---

## Using the Telemetry File

Every session creates a detailed telemetry log at: `extras/telemetry.md`

This file contains:
- All STT transcriptions with confidence scores
- All commands matched/unrecognized
- All actions executed
- Execution success/failure
- Full chronological timeline

**Use this to:**
- Debug why a command isn't working
- See what STT is actually hearing
- Find patterns in recognition failures
- Share with support when asking for help

## Tips for Reaper Power Users

### Using SWS Actions

SWS extension actions use string IDs instead of numbers:

```yaml
  insert_marker:
    patterns:
      - "insert marker"
      - "add marker"
    action_name: "SWS/S&M: Insert marker at edit cursor"
    description: "Insert marker at edit cursor"
    available_during_recording: false
```

Action name: `SWS/S&M: Insert marker at edit cursor`
Action ID: `_S&M_INS_MARKER_EDIT` (string, not number)

The system handles both automatically!

### Action Context Matters

Some actions have the same name but different contexts:

```
Main	1016	Transport: Stop
MIDI Editor	1142	Transport: Stop
```

The action mapper **prioritizes "Main" section actions** automatically. If you need a MIDI Editor action specifically, you may need to use the numeric ID instead of the action name.

---

## Command Ideas to Get You Started

Here are some useful commands you might want to add:

```yaml
  # Rendering
  render:
    patterns:
      - "render"
      - "export"
      - "bounce"
    action_name: "File: Render project, using the most recent render settings"
    description: "Render project"
    available_during_recording: false

  # Loop
  toggle_loop:
    patterns:
      - "loop"
      - "toggle loop"
    action_name: "Transport: Toggle repeat"
    description: "Toggle loop on/off"
    available_during_recording: false

  # Redo
  redo:
    patterns:
      - "redo"
      - "redo that"
    action_name: "Edit: Redo"
    description: "Redo last undone action"
    available_during_recording: false

  # Zoom
  zoom_selection:
    patterns:
      - "zoom to selection"
      - "zoom selection"
    action_name: "View: Zoom to selected items"
    description: "Zoom to selected items"
    available_during_recording: false
```

## Getting Help

If you're stuck:

1. **Check the telemetry** - It shows exactly what's happening
2. **Read `extras/telemetry.md`** - Full session log with timestamps
3. **Verify action name** - Must match `reaper-actions.txt` exactly
4. **Test patterns** - Speak them and watch what STT hears

**The telemetry is your debugging superpower - use it!**

## Summary Checklist

When adding a custom command:

- [ ] Run ReaperVC and speak the phrase - verify STT hears it correctly
- [ ] Find the action name in Reaper action list
- [ ] Add command to `config/transport_commands.yaml`
- [ ] Restart ReaperVC and check for action resolution errors
- [ ] Test the command and watch the telemetry
- [ ] Verify the action executed in Reaper
- [ ] Check `extras/telemetry.md` if something went wrong

**Happy commanding!** 🎙️
