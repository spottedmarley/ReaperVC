#!/usr/bin/env python3
"""
ReaperVC - Voice Control for REAPER
Direct voice command execution via OSC - fully customizable
"""

import sys
import signal
import yaml
import time
from pathlib import Path
from pythonosc import udp_client
from voice.voice_input import VoiceInput
from voice.audio_feedback import AudioFeedback
from action_mapper import ActionMapper
from telemetry import Telemetry
from number_extractor import NumberExtractor
from keyboard_input import KeyboardInput
from command_list_gui import launch_command_list

# ANSI Colors
class Colors:
	@staticmethod
	def green(text): return f"\033[92m{text}\033[0m"
	@staticmethod
	def red(text): return f"\033[91m{text}\033[0m"
	@staticmethod
	def yellow(text): return f"\033[93m{text}\033[0m"
	@staticmethod
	def blue(text): return f"\033[94m{text}\033[0m"
	@staticmethod
	def cyan(text): return f"\033[96m{text}\033[0m"


class ReaperVCController:
	"""
	Voice control for REAPER via OSC
	Direct command matching - customizable voice commands
	"""

	def __init__(self, config_path=None):
		"""Initialize ReaperVC controller"""
		print(Colors.blue("\n[+] Initializing ReaperVC..."))

		# Initialize telemetry
		self.telemetry = Telemetry()
		self.telemetry.clear()
		self.telemetry.log("System", "ReaperVC starting...")

		# Load config
		if config_path is None:
			config_path = Path(__file__).parent.parent / "config" / "config.yaml"

		with open(config_path, 'r') as f:
			self.config = yaml.safe_load(f)

		# Load action mapper
		reaper_actions_path = Path(__file__).parent.parent / "reaper-actions.txt"
		self.action_mapper = ActionMapper(reaper_actions_path)

		# Load default commands
		commands_path = Path(__file__).parent.parent / "config" / "default_commands.yaml"
		with open(commands_path, 'r') as f:
			self.commands_config = yaml.safe_load(f)

		# Load custom commands (optional - can override defaults)
		custom_commands_path = Path(__file__).parent.parent / "config" / "custom_commands.yaml"
		if custom_commands_path.exists():
			print(Colors.blue("[+] Loading custom commands..."))
			with open(custom_commands_path, 'r') as f:
				custom_config = yaml.safe_load(f)
				if custom_config and 'commands' in custom_config:
					# Merge custom commands into main config (custom overwrites defaults)
					for cmd_name, cmd_config in custom_config['commands'].items():
						if cmd_name in self.commands_config['commands']:
							print(Colors.yellow(f"  Overriding: {cmd_name}"))
						else:
							print(Colors.green(f"  Adding: {cmd_name}"))
						self.commands_config['commands'][cmd_name] = cmd_config

		# Resolve action names to IDs
		self._resolve_action_names()

		# OSC setup
		osc_config = self.config['osc']
		self.osc = udp_client.SimpleUDPClient(
			osc_config['host'],
			osc_config['reaper_port']
		)
		print(Colors.green(f"[+] OSC connected to {osc_config['host']}:{osc_config['reaper_port']}"))

		# Voice input - pass voice config path
		voice_config_path = Path(__file__).parent.parent / "config" / "voice_config.yaml"
		self.voice = VoiceInput(str(voice_config_path))
		print(Colors.green("[+] Voice input initialized"))

		# Audio feedback
		self.audio_feedback = AudioFeedback()
		print(Colors.green("[+] Audio feedback initialized"))

		# Number extractor for parameterized commands
		self.number_extractor = NumberExtractor()

		# Keyboard input for typing text
		try:
			self.keyboard = KeyboardInput()
			if self.keyboard.available:
				print(Colors.green("[+] Keyboard input initialized"))
		except Exception as e:
			print(Colors.yellow(f"[!] Keyboard input initialization failed: {e}"))
			print(Colors.yellow("[!] Text input commands will be disabled"))

		self.is_running = False
		self.is_recording = False  # Track recording state
		self.is_playing = False    # Track playback state
		self.stats = {
			'commands_executed': 0,
			'commands_failed': 0,
			'unrecognized': 0
		}

		# Command debouncing - prevent duplicate commands
		self.last_command_time = {}
		self.command_cooldown = 1.0  # seconds

	def _resolve_action_names(self):
		"""
		Resolve action names to action IDs using the action mapper
		Modifies commands_config in place
		Skips resolution if 'action' or 'actions' already set (for custom commands with explicit IDs)
		"""
		for cmd_name, cmd_config in self.commands_config['commands'].items():
			# Single action
			if 'action_name' in cmd_config:
				# Skip if action ID already set (custom command with explicit ID)
				if 'action' in cmd_config:
					print(f"  {cmd_name}: Using explicit action ID → {cmd_config['action']}")
					continue

				action_name = cmd_config['action_name']
				try:
					action_id = self.action_mapper.resolve_action(action_name)
					cmd_config['action'] = action_id
					print(f"  {cmd_name}: {action_name} → {action_id}")
				except ValueError as e:
					print(Colors.red(f"  [ERROR] {cmd_name}: {e}"))
					raise

			# Multiple actions
			if 'action_names' in cmd_config:
				# Skip if action IDs already set (custom command with explicit IDs)
				if 'actions' in cmd_config:
					print(f"  {cmd_name}: Using explicit action IDs → {cmd_config['actions']}")
					continue

				action_names = cmd_config['action_names']
				try:
					action_ids = self.action_mapper.resolve_actions(action_names)
					cmd_config['actions'] = action_ids
					print(f"  {cmd_name}: {len(action_ids)} actions resolved")
				except ValueError as e:
					print(Colors.red(f"  [ERROR] {cmd_name}: {e}"))
					raise

	def match_command(self, text):
		"""
		Match spoken text to a command using simple pattern matching
		Returns: (command_name, confidence, parameter) or (None, 0, None)
		parameter is dict: {'type': 'bpm', 'value': 120} or None
		"""
		# Normalize text: lowercase, keep only alphanumeric and spaces
		import re
		text = text.lower()
		text = re.sub(r'[^a-z0-9\s]', '', text)
		text = text.strip()

		# Phonetic corrections for common misrecognitions
		phonetic_fixes = {
			'traygon': 'try again',
			'traygan': 'try again',
			'traygen': 'try again',
			'try it again': 'try again',
			'reccord': 'record',
			'recordd': 'record',
			'start': 'record',  # "start" often means "record" in context
			'reed wind': 'rewind',
			'playy': 'play',
			'playe': 'play',
			'stopp': 'stop',
			'stahp': 'stop',
			'metronome on': 'metronome',
			'metronome off': 'metronome',
			'click on': 'metronome',
			'click off': 'metronome',
		}

		# Apply phonetic corrections
		if text in phonetic_fixes:
			original_text = text
			text = phonetic_fixes[text]
			print(Colors.yellow(f"[Phonetic] '{original_text}' → '{text}'"))
			self.telemetry.log("Phonetic", f"Corrected: '{original_text}' → '{text}'")

		best_match = None
		best_confidence = 0
		best_pattern_length = 0

		# Try to match against all command patterns
		for cmd_name, cmd_config in self.commands_config['commands'].items():
			patterns = cmd_config['patterns']

			# Check if command is available during recording
			available_during_recording = cmd_config.get('available_during_recording', True)
			if self.is_recording and not available_during_recording:
				# Skip commands not available during recording
				continue

			# Exact match - highest priority
			if text in patterns:
				# Check if this command needs a parameter
				param_type = cmd_config.get('parameter_type')
				if param_type:
					parameter = self._extract_parameter(text, param_type)
					return (cmd_name, 1.0, parameter)
				else:
					return (cmd_name, 1.0, None)

			# Partial match (text contains pattern)
			for pattern in patterns:
				if pattern in text:
					# Prefer longer pattern matches (more specific)
					# "start recording" should match "start recording" over "start"
					pattern_len = len(pattern)
					if pattern_len > best_pattern_length:
						best_match = cmd_name
						best_confidence = 0.8
						best_pattern_length = pattern_len

		if best_match:
			# Check if this command needs a parameter
			cmd_config = self.commands_config['commands'][best_match]
			param_type = cmd_config.get('parameter_type')

			if param_type:
				# Extract parameter from original text (before normalization)
				parameter = self._extract_parameter(text, param_type)
				return (best_match, best_confidence, parameter)
			else:
				return (best_match, best_confidence, None)

		return (None, 0, None)

	def _extract_parameter(self, text, param_type):
		"""
		Extract parameter from command text

		Args:
			text: Normalized command text
			param_type: Type of parameter ('bpm', 'time', etc.)

		Returns:
			dict: {'type': param_type, 'value': extracted_value} or None
		"""
		if param_type == 'bpm':
			bpm = self.number_extractor.extract_bpm(text)
			if bpm is not None:
				return {'type': 'bpm', 'value': bpm}
			else:
				return None

		elif param_type == 'time':
			time_seconds = self.number_extractor.extract_time(text)
			if time_seconds is not None:
				return {'type': 'time', 'value': time_seconds}
			else:
				return None

		elif param_type == 'pan_left':
			# Extract percentage and calculate normalized MIDI CC value (0.0-1.0)
			# MIDI CC: 0=left, 64=center, 127=right
			# Normalize by dividing by 127
			# Formula: (64 - (percentage * 0.64)) / 127
			# Example: 50% left = (64 - 32) / 127 = 32 / 127 = 0.252
			percentage = self.number_extractor.extract_pan_percentage(text)
			if percentage is not None:
				midi_value = 64 - (percentage * 0.64)
				# Normalize to 0.0-1.0 range
				pan_value = midi_value / 127.0
				# Clamp to valid range
				pan_value = max(0.0, min(1.0, pan_value))
				return {'type': 'pan_left', 'value': pan_value}
			else:
				return None

		elif param_type == 'pan_right':
			# Extract percentage and calculate normalized MIDI CC value (0.0-1.0)
			# MIDI CC: 0=left, 64=center, 127=right
			# Normalize by dividing by 127
			# Formula: (64 + (percentage * 0.63)) / 127
			# Example: 50% right = (64 + 31.5) / 127 = 95 / 127 = 0.748
			percentage = self.number_extractor.extract_pan_percentage(text)
			if percentage is not None:
				midi_value = 64 + (percentage * 0.63)
				# Normalize to 0.0-1.0 range
				pan_value = midi_value / 127.0
				# Clamp to valid range
				pan_value = max(0.0, min(1.0, pan_value))
				return {'type': 'pan_right', 'value': pan_value}
			else:
				return None

		elif param_type == 'pan_center':
			# Pan center is MIDI CC 64, normalized = 64/127 = 0.504
			return {'type': 'pan_center', 'value': 64.0 / 127.0}

		return None

	def execute_command(self, command_name, parameter=None):
		"""
		Execute a command by sending OSC action(s)

		Args:
			command_name: Name of the command to execute
			parameter: Optional parameter dict (e.g., {'type': 'bpm', 'value': 120})
		"""
		cmd_config = self.commands_config['commands'][command_name]
		description = cmd_config['description']

		# Handle command_list - launch GUI window
		if command_name == 'command_list':
			print(Colors.blue("\n[+] Launching command list window..."))
			self.telemetry.log("System", "Launching command list window")
			try:
				launch_command_list(self.commands_config)
				print(Colors.green("[OK] Command list window launched"))
				self.telemetry.log("System", "[OK] Command list window launched")
				self.audio_feedback.play_action_complete()
				return True
			except Exception as e:
				print(Colors.red(f"[ERROR] Failed to launch command list: {e}"))
				self.telemetry.log("Error", f"Failed to launch command list: {e}")
				self.audio_feedback.play_error()
				return False

		# Handle kill command - immediate exit
		if command_name == 'kill_reapervc':
			print(Colors.red("\n[!] Kill command received - shutting down immediately"))
			self.telemetry.log("System", "Kill command received - immediate shutdown")

			# Give telemetry a moment to write the shutdown message
			import time
			time.sleep(0.15)

			# Signal telemetry monitor to stop by writing flag file
			try:
				import os
				flag_file = "/tmp/reapervc_stop_telemetry"
				with open(flag_file, 'w') as f:
					f.write("stop")
				print("Signaling telemetry monitor to stop...")
				# Give telemetry script time to see the flag
				time.sleep(0.2)
			except Exception as e:
				print(f"Note: Could not signal telemetry monitor: {e}")

			# Play shutdown sound
			try:
				self.audio_feedback.play_shutdown()
			except Exception:
				pass  # Don't let audio errors prevent shutdown

			# Cleanup and exit
			self.stop()

			# Give threads time to clean up
			import time
			time.sleep(0.5)

			sys.exit(0)

		# Update playback/recording state based on command
		if command_name == 'play':
			self.is_playing = True
			self.is_recording = False
			print(Colors.yellow("[State] Playing"))
			self.telemetry.log("State", "Playback state: Playing")
		elif command_name == 'record':
			self.is_recording = True
			self.is_playing = False
			print(Colors.yellow("[State] Recording"))
			self.telemetry.log("State", "Playback state: Recording")
		elif command_name == 'stop':
			self.is_recording = False
			self.is_playing = False
			print(Colors.yellow("[State] Stopped"))
			self.telemetry.log("State", "Playback state: Stopped")
		elif command_name == 'pause':
			# Pause doesn't change recording/playing flags, just pauses current state
			print(Colors.yellow("[State] Paused"))
			self.telemetry.log("State", "Playback state: Paused")

		# Handle OSC message with parameter (e.g., set tempo)
		if 'osc_message' in cmd_config:
			osc_path = cmd_config['osc_message']

			# Check if parameter was provided
			if parameter is None:
				print(Colors.red(f"[ERROR] {description} requires a parameter"))
				self.telemetry.log("Error", f"{description} - parameter missing")
				self.audio_feedback.play_error()
				return False

			param_value = parameter['value']
			param_type = parameter['type']

			# Send OSC message with parameter
			print(Colors.blue(f"[→] {description}: {param_value}"))
			self.telemetry.log("Reaper", f"[→] Sending {osc_path} with value: {param_value}")
			self.osc.send_message(osc_path, [float(param_value)])
			print(Colors.green(f"[OK] {description}: {param_value}"))
			self.telemetry.log("Reaper", f"[OK] {description}: {param_value}")
			self.audio_feedback.play_action_complete()
			return True

		# Handle null action (confirmation only)
		if cmd_config.get('action') is None and cmd_config.get('actions') is None:
			print(Colors.green(f"[OK] {description}"))
			self.telemetry.log("Reaper", f"[OK] {description} (null action - confirmation only)")
			self.audio_feedback.play_action_complete()
			return True

		# Single action
		if 'action' in cmd_config:
			action_id = cmd_config['action']
			print(Colors.blue(f"[→] {description}"))
			self.telemetry.log("Reaper", f"[→] Sending action {action_id}: {description}")

			# For string-based command IDs (SWS extensions), send as string parameter
			if isinstance(action_id, str) and action_id.startswith('_'):
				self.osc.send_message("/action/str", [action_id])
			else:
				self.osc.send_message(f"/action/{action_id}", [])

			# Handle text input after action (if specified)
			if 'text_input' in cmd_config:
				text = cmd_config['text_input']
				delay = cmd_config.get('text_delay', 0.2)
				print(Colors.blue(f"[⌨] Typing: {text}"))
				self.telemetry.log("Keyboard", f"Typing: {text}")
				if hasattr(self, 'keyboard') and self.keyboard.type_text(text, delay):
					print(Colors.green(f"[OK] Typed: {text}"))
					self.telemetry.log("Keyboard", f"[OK] Typed: {text}")
				else:
					print(Colors.red(f"[!] Failed to type text (keyboard disabled)"))
					self.telemetry.log("Keyboard", f"[ERROR] Failed to type text")

			# Handle key press after text input (if specified)
			if 'press_key' in cmd_config:
				key = cmd_config['press_key']
				key_delay = cmd_config.get('key_delay', 0.05)
				print(Colors.blue(f"[⌨] Pressing key: {key}"))
				self.telemetry.log("Keyboard", f"Pressing key: {key}")
				if hasattr(self, 'keyboard') and self.keyboard.press_key(key, key_delay):
					print(Colors.green(f"[OK] Pressed: {key}"))
					self.telemetry.log("Keyboard", f"[OK] Pressed: {key}")
				else:
					print(Colors.red(f"[!] Failed to press key (keyboard disabled)"))
					self.telemetry.log("Keyboard", f"[ERROR] Failed to press key")

			print(Colors.green(f"[OK] {description}"))
			self.telemetry.log("Reaper", f"[OK] {description}")
			self.audio_feedback.play_action_complete()
			return True

		# Multiple actions (sequence)
		if 'actions' in cmd_config:
			print(Colors.blue(f"[→] {description}"))
			self.telemetry.log("Reaper", f"[→] Sending {len(cmd_config['actions'])} actions: {description}")
			for i, action_id in enumerate(cmd_config['actions'], 1):
				self.telemetry.log("Reaper", f"  Action {i}/{len(cmd_config['actions'])}: {action_id}")

				# For string-based command IDs (SWS extensions), send as string parameter
				if isinstance(action_id, str) and action_id.startswith('_'):
					self.osc.send_message("/action/str", [action_id])
				else:
					self.osc.send_message(f"/action/{action_id}", [])

				time.sleep(0.1)  # Small delay between actions

			# Handle text input after actions (if specified)
			if 'text_input' in cmd_config:
				text = cmd_config['text_input']
				delay = cmd_config.get('text_delay', 0.2)
				print(Colors.blue(f"[⌨] Typing: {text}"))
				self.telemetry.log("Keyboard", f"Typing: {text}")
				if hasattr(self, 'keyboard') and self.keyboard.type_text(text, delay):
					print(Colors.green(f"[OK] Typed: {text}"))
				else:
					print(Colors.red(f"[!] Failed to type text (keyboard disabled)"))

			# Handle key press after text input (if specified)
			if 'press_key' in cmd_config:
				key = cmd_config['press_key']
				key_delay = cmd_config.get('key_delay', 0.05)
				print(Colors.blue(f"[⌨] Pressing key: {key}"))
				self.telemetry.log("Keyboard", f"Pressing key: {key}")
				if hasattr(self, 'keyboard') and self.keyboard.press_key(key, key_delay):
					print(Colors.green(f"[OK] Pressed: {key}"))
					self.telemetry.log("Keyboard", f"[OK] Pressed: {key}")
				else:
					print(Colors.red(f"[!] Failed to press key (keyboard disabled)"))
					self.telemetry.log("Keyboard", f"[ERROR] Failed to press key")

			print(Colors.green(f"[OK] {description}"))
			self.telemetry.log("Reaper", f"[OK] {description}")
			self.audio_feedback.play_action_complete()
			return True

		return False

	def process_voice_command(self, text):
		"""
		Process a voice command
		"""
		print(f"\n{Colors.cyan('[Voice]')} '{text}'")
		self.telemetry.log("Spoken", f"Received: '{text}'")

		# Match command
		command_name, confidence, parameter = self.match_command(text)

		if command_name is None:
			print(Colors.yellow(f"[?] Unrecognized command: '{text}'"))
			self.telemetry.log("Command", f"Unrecognized: '{text}'")
			self.audio_feedback.play_command_failed()
			self.stats['unrecognized'] += 1
			return

		# Show matched command with parameter if present
		if parameter:
			param_str = f" ({parameter['type']}={parameter['value']})"
			print(Colors.blue(f"[Match] {command_name}{param_str} (confidence: {confidence:.2f})"))
			self.telemetry.log("Command", f"Matched: {command_name}{param_str} (confidence: {confidence:.2f})")
		else:
			print(Colors.blue(f"[Match] {command_name} (confidence: {confidence:.2f})"))
			self.telemetry.log("Command", f"Matched: {command_name} (confidence: {confidence:.2f})")

		# Check for duplicate command (debouncing)
		current_time = time.time()
		last_time = self.last_command_time.get(command_name, 0)
		time_since_last = current_time - last_time

		if time_since_last < self.command_cooldown:
			print(Colors.yellow(f"[Debounce] Ignoring duplicate '{command_name}' ({time_since_last:.2f}s since last)"))
			self.telemetry.log("Debounce", f"Ignored duplicate: {command_name} ({time_since_last:.2f}s since last)")
			return

		self.last_command_time[command_name] = current_time

		# Execute command
		try:
			success = self.execute_command(command_name, parameter)
			if success:
				self.stats['commands_executed'] += 1
				self.telemetry.log("Result", f"Success: {command_name}")
			else:
				self.stats['commands_failed'] += 1
				self.telemetry.log("Result", f"Failed: {command_name}")
		except Exception as e:
			print(Colors.red(f"[ERROR] Command execution failed: {e}"))
			self.telemetry.log("Error", f"Command execution failed: {command_name} - {e}")
			self.audio_feedback.play_error()
			self.stats['commands_failed'] += 1

	def _check_external_commands(self):
		"""Check for external command trigger file"""
		trigger_file = Path("/tmp/reapervc_external_command")
		if trigger_file.exists():
			try:
				with open(trigger_file, 'r') as f:
					command_text = f.read().strip()
				# Delete the file
				trigger_file.unlink()
				# Process the command
				if command_text:
					print(Colors.cyan(f"\n[External] Command received: '{command_text}'"))
					self.telemetry.log("External", f"Received: '{command_text}'")
					self.process_voice_command(command_text)
			except Exception as e:
				print(Colors.yellow(f"[!] Error reading external command: {e}"))

	def start(self):
		"""Start the controller"""
		print("\n" + "="*50)
		print(Colors.green("[+] ReaperVC Ready!"))
		print("="*50)
		print(Colors.blue("\nAvailable commands:"))
		for cmd_name, cmd_config in self.commands_config['commands'].items():
			print(f"  • {Colors.yellow(cmd_name)}: {cmd_config['description']}")
			print(f"    Patterns: {', '.join(cmd_config['patterns'][:3])}")
		print("\n" + "="*50)
		print(Colors.green("[+] Listening for commands...\n"))

		# Start voice input first
		self.voice.start()

		# Set up telemetry callback
		self.voice.set_telemetry_callback(lambda cat, msg: self.telemetry.log(cat, msg))

		# Then set up voice callback (starts callback thread)
		self.voice.set_command_callback(self.process_voice_command)

		self.is_running = True

		# Main loop (check for external commands periodically)
		try:
			while self.is_running:
				self._check_external_commands()
				time.sleep(0.1)
		except KeyboardInterrupt:
			pass

	def stop(self):
		"""Stop the controller"""
		if not self.is_running:
			return

		print("\n[+] Stopping ReaperVC...")
		self.is_running = False

		self.voice.stop()

		# Print statistics
		print("\n[Stats] Session statistics:")
		print(f"   Commands executed: {self.stats['commands_executed']}")
		print(f"   Commands failed: {self.stats['commands_failed']}")
		print(f"   Unrecognized: {self.stats['unrecognized']}")

		# Write telemetry
		self.telemetry.log("System", f"Session stats - Executed: {self.stats['commands_executed']}, Failed: {self.stats['commands_failed']}, Unrecognized: {self.stats['unrecognized']}")
		try:
			import os
			script_dir = Path(os.path.abspath(__file__)).parent.parent
			telemetry_path = script_dir / "extras" / "telemetry.md"
			self.telemetry.write_to_file(telemetry_path)
			print(f"[+] Telemetry saved to {telemetry_path}")
		except Exception as e:
			print(Colors.yellow(f"[!] Could not save telemetry file: {e}"))

		print("\n[+] Goodbye!")


def main():
	"""Main entry point"""
	# Check if ReaperVC is already running
	import subprocess
	try:
		result = subprocess.run(
			["pgrep", "-f", "reapervc.py"],
			capture_output=True,
			text=True
		)
		# If pgrep found processes
		if result.stdout.strip():
			pids = result.stdout.strip().split('\n')
			current_pid = str(subprocess.os.getpid())
			# Filter out current process
			other_pids = [pid for pid in pids if pid != current_pid]
			if other_pids:
				print(Colors.yellow("[!] ReaperVC is already running (PID: {})".format(', '.join(other_pids))))
				print(Colors.yellow("[!] Aborting to prevent duplicate instances"))
				sys.exit(0)
	except Exception as e:
		# If check fails, continue anyway (better to start than fail)
		print(Colors.yellow(f"[!] Could not check for existing instances: {e}"))

	app = None

	def signal_handler(sig, frame):
		"""Handle Ctrl+C gracefully"""
		print("\n\n⚡ Interrupt received (CTRL+C)...")
		if app:
			app.stop()
		sys.exit(0)

	# Set up signal handler
	signal.signal(signal.SIGINT, signal_handler)
	signal.signal(signal.SIGTERM, signal_handler)

	# Start application
	app = ReaperVCController()

	try:
		app.start()
	except Exception as e:
		print(f"[FATAL] {e}")
		import traceback
		traceback.print_exc()
	finally:
		if app:
			app.stop()


if __name__ == "__main__":
	main()
