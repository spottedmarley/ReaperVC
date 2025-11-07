# OSC Message Reference

Complete reference for OSC messages used in ReaperVC

---

## OSC Basics

### Message Format
```
/address [arg1] [arg2] ...
```

### Ports
- **Reaper listens on**: `8000` (receives commands from ReaperVC)
- **ReaperVC listens on**: `9000` (receives feedback from Reaper)
- **Protocol**: UDP (localhost only for security)

---

## Transport Control

### Play

**Address**: `/action/1007` or `/play`

**Arguments**: None

**Description**: Start playback from current position

**Example**:
```python
osc.send("/action/1007")
```

### Stop

**Address**: `/action/1016` or `/stop`

**Arguments**: None

**Description**: Stop playback and recording

**Example**:
```python
osc.send("/action/1016")
```

### Record

**Address**: `/action/1013` or `/record`

**Arguments**: None

**Description**: Start recording on armed tracks

**Example**:
```python
osc.send("/action/1013")
```

### Pause

**Address**: `/action/1008` or `/pause`

**Arguments**: None

**Description**: Pause playback (play again to resume)

**Example**:
```python
osc.send("/action/1008")
```

### Toggle Repeat

**Address**: `/action/1068`

**Arguments**: None

**Description**: Toggle repeat mode on/off

---

## Track Operations

### Track Numbering
Tracks are numbered starting from 1 (track 1, track 2, etc.)

### Set Track Volume

**Address**: `/track/<n>/volume`

**Arguments**:
- `volume` (float): 0.0 to 2.0
	- 0.0 = -inf dB (silence)
	- 1.0 = 0 dB (unity)
	- 2.0 = +6 dB

**Description**: Set volume for track N

**Example**:
```python
# Set track 1 to -6dB (volume = 0.5)
osc.send("/track/1/volume", 0.5)

# Set track 2 to 0dB (unity)
osc.send("/track/2/volume", 1.0)
```

**dB to Volume Conversion**:
```python
volume = 10 ** (db / 20.0)

# Examples:
# -6 dB → 0.501
# 0 dB → 1.0
# +6 dB → 1.995
```

### Set Track Pan

**Address**: `/track/<n>/pan`

**Arguments**:
- `pan` (float): -1.0 to 1.0
	- -1.0 = 100% left
	- 0.0 = center
	- 1.0 = 100% right

**Description**: Set pan for track N

**Example**:
```python
# Pan track 1 hard left
osc.send("/track/1/pan", -1.0)

# Pan track 2 center
osc.send("/track/2/pan", 0.0)
```

### Set Track Name

**Address**: `/track/<n>/name`

**Arguments**:
- `name` (string): Track name

**Description**: Rename track N

**Example**:
```python
osc.send("/track/1/name", "Vocal")
osc.send("/track/2/name", "Guitar")
```

### Mute Track

**Address**: `/track/<n>/mute`

**Arguments**:
- `state` (int): 0 = unmute, 1 = mute

**Description**: Mute or unmute track N

**Example**:
```python
# Mute track 1
osc.send("/track/1/mute", 1)

# Unmute track 1
osc.send("/track/1/mute", 0)
```

### Solo Track

**Address**: `/track/<n>/solo`

**Arguments**:
- `state` (int): 0 = unsolo, 1 = solo

**Description**: Solo or unsolo track N

**Example**:
```python
# Solo track 2
osc.send("/track/2/solo", 1)
```

### Select Track

**Address**: `/track/<n>/select`

**Arguments**:
- `state` (int): 0 = deselect, 1 = select

**Description**: Select or deselect track N

**Example**:
```python
# Select track 1
osc.send("/track/1/select", 1)

# Deselect all, then select track 3
osc.send("/track/1/select", 0)
osc.send("/track/2/select", 0)
osc.send("/track/3/select", 1)
```

### Arm Track for Recording

**Address**: `/track/<n>/recarm`

**Arguments**:
- `state` (int): 0 = disarm, 1 = arm

**Description**: Arm or disarm track N for recording

**Example**:
```python
# Arm track 1
osc.send("/track/1/recarm", 1)

# Disarm track 1
osc.send("/track/1/recarm", 0)
```

---

## Actions (by Command ID)

### Format

**Address**: `/action/<command_id>`

**Arguments**: None (or 1 for "on", 0 for "off" for toggle actions)

**Description**: Execute Reaper action by command ID

### Common Action IDs

#### Transport
- `1007` - Play
- `1008` - Pause
- `1013` - Record
- `1016` - Stop
- `1068` - Toggle repeat

#### Track Management
- `40001` - Insert new track
- `40005` - Remove selected tracks
- `40297` - Unselect all tracks
- `40001` - Insert new track at end
- `40062` - Insert new track above selected
- `6` - Toggle mute for selected tracks
- `7` - Toggle solo for selected tracks
- `40294` - Toggle record arm for selected tracks

#### Edit
- `40029` - Undo
- `40030` - Redo
- `40058` - Copy items
- `40057` - Cut items
- `42398` - Paste items

#### Markers
- `40157` - Insert marker at current position
- `40172` - Go to previous marker
- `40173` - Go to next marker

#### View
- `40913` - Vertical scroll selected tracks into view
- `40295` - Zoom out horizontal
- `40296` - Zoom in horizontal

### Finding Action IDs

In Reaper:
1. **Actions → Show action list**
2. Find the action you want
3. Right-click → **Copy selected action command ID**

---

## Feedback Messages (Reaper → ReaperVC)

Reaper sends feedback about state changes. These are received on port 9000.

### Track Volume Feedback

**Address**: `/track/<n>/volume`

**Arguments**: `volume` (float)

**When sent**: Track volume changes

### Track Mute Feedback

**Address**: `/track/<n>/mute`

**Arguments**: `state` (int): 0 or 1

**When sent**: Track mute state changes

### Transport State Feedback

**Address**: `/play`, `/stop`, `/record`

**Arguments**: `state` (int): 0 or 1

**When sent**: Transport state changes

---

## Advanced Patterns

### Wildcard Matching

The pattern file supports wildcards:

```
TRACK_VOLUME "/track/@/volume"
```

`@` matches any track number.

### Bank/Send/Receive

```
/track/<n>/send/<send_id>/volume <value>
/track/<n>/recv/<recv_id>/volume <value>
```

### FX Parameters

```
/track/<n>/fx/<fx_id>/param/<param_id>/value <value>
```

Example:
```python
# Set FX 1, parameter 3 to 0.75 on track 1
osc.send("/track/1/fx/1/param/3/value", 0.75)
```

---

## Custom Pattern File

The file `config/default.ReaperOSC` defines message patterns.

### Basic Format

```
# Comment
DEVICE_NAME "ReaperVC"

# Transport
TRANSPORT_PLAY "/play"
TRANSPORT_STOP "/stop"

# Track control
TRACK_VOLUME "/track/@/volume"
TRACK_MUTE "/track/@/mute"
```

### Feedback Configuration

```
REAPER_TRACK_FOLLOWS DEVICE
```

This makes Reaper send feedback when values change.

---

## Python OSC Examples

### Basic Usage

```python
from pythonosc import udp_client

client = udp_client.SimpleUDPClient("127.0.0.1", 8000)

# Play
client.send_message("/action/1007", [])

# Set track 1 volume to -6dB
client.send_message("/track/1/volume", [0.5])

# Mute track 2
client.send_message("/track/2/mute", [1])
```

### Receiving Feedback

```python
from pythonosc import dispatcher, osc_server

def volume_handler(address, *args):
	print(f"Volume changed: {address} = {args[0]}")

disp = dispatcher.Dispatcher()
disp.map("/track/*/volume", volume_handler)

server = osc_server.ThreadingOSCUDPServer(("127.0.0.1", 9000), disp)
server.serve_forever()
```

---

## Debugging OSC

### Enable Reaper OSC Logging

In Reaper:
- **Options → Preferences → Control/OSC/web**
- Check **Log incoming OSC messages**
- Check **Log outgoing OSC messages**
- Messages appear in Reaper's ReaScript console

### Monitor Traffic

Use `tcpdump` to watch OSC traffic:

```bash
sudo tcpdump -i lo -n port 8000 or port 9000
```

### Test with Command Line

Use `sendosc` utility:

```bash
# Install
sudo apt-get install sendosc

# Send message
sendosc localhost 8000 /action/1007
```

---

## References

- [Official Reaper OSC Documentation](https://www.reaper.fm/sdk/osc/osc.php)
- [Reaper Action List](https://www.reaper.fm/sdk/reascript/reascripthelp.html#Action_List)
- [python-osc Documentation](https://python-osc.readthedocs.io/)

---

## Quick Reference Table

| Action | OSC Address | Arguments |
|--------|-------------|-----------|
| Play | `/action/1007` | - |
| Stop | `/action/1016` | - |
| Record | `/action/1013` | - |
| New Track | `/action/40001` | - |
| Set Volume | `/track/<n>/volume` | 0.0-2.0 |
| Set Pan | `/track/<n>/pan` | -1.0 to 1.0 |
| Mute | `/track/<n>/mute` | 0 or 1 |
| Solo | `/track/<n>/solo` | 0 or 1 |
| Arm | `/track/<n>/recarm` | 0 or 1 |
| Set Name | `/track/<n>/name` | string |
