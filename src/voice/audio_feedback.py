"""
Audio Feedback Module
Provides audible signals for user feedback
"""

import numpy as np
import sounddevice as sd
import time
import atexit

# Prevent PortAudio termination error on exit
def _cleanup_audio():
	try:
		sd._terminate()
	except:
		pass

atexit.unregister(sd._exit_handler)
atexit.register(_cleanup_audio)


class AudioFeedback:
	"""
	Generates and plays audio feedback signals
	"""

	def __init__(self, sample_rate=44100):
		self.sample_rate = sample_rate
		self.volume = 0.3  # 30% volume
		self.audio_working = True  # Flag to track if audio output works

		# Detect if JACK is running
		import os
		import subprocess
		from pathlib import Path
		self.use_jack = False

		# Check if JACK is running by looking for jack processes
		try:
			result = subprocess.run(['pgrep', '-x', 'jackd'], capture_output=True)
			if result.returncode == 0:
				self.use_jack = True
				print("[Audio] JACK detected - using direct JACK client")
		except:
			pass

		self.output_device = None

		if not self.use_jack:
			# Normal mode: Use sounddevice directly
			try:
				import sounddevice as sd
				devices = sd.query_devices()
				# Look for 'default' or 'pulse' ALSA device
				for i, dev in enumerate(devices):
					if dev['max_output_channels'] > 0:
						if 'default' in dev['name'].lower() or 'pulse' in dev['name'].lower():
							self.output_device = i
							print(f"[Audio] Using device [{i}]: {dev['name']}")
							break

				if self.output_device is None:
					# Fallback to first output device
					for i, dev in enumerate(devices):
						if dev['max_output_channels'] > 0:
							self.output_device = i
							print(f"[Audio] Using fallback device [{i}]: {dev['name']}")
							break
			except Exception as e:
				print(f"[Audio] Error finding device: {e}")

		# Load custom audio files if available
		self.sounds_dir = Path(__file__).parent.parent.parent / "sounds"
		self.audio_files = {
			'welcome': self.sounds_dir / "welcome.wav",
			'action_complete': self.sounds_dir / "action-complete.wav",
			'shutdown': self.sounds_dir / "shutdown.wav",
			'command_failed': self.sounds_dir / "command-failed.wav"
		}

		# Test audio on init - play welcome sound
		print("[Audio] Testing audio output...")
		self._test_audio()

	def _test_audio(self):
		"""Play welcome sound to verify audio is working"""
		try:
			# Try to play welcome.wav if it exists
			if self.audio_files['welcome'].exists():
				self._play_wav_file('welcome')
				print("[Audio] Welcome sound played - audio working!")
			else:
				# Fallback to generated tone
				if self.use_jack:
					self._play_tone_jack(880, 0.1)
				else:
					# Quick 100ms beep using sounddevice
					duration = 0.1
					frequency = 880
					t = np.linspace(0, duration, int(self.sample_rate * duration))
					tone = 0.2 * np.sin(2 * np.pi * frequency * t)

					# Quick fade to prevent clicks
					fade_samples = int(0.02 * self.sample_rate)
					if fade_samples > 0:
						fade_in = np.linspace(0, 1, fade_samples)
						fade_out = np.linspace(1, 0, fade_samples)
						tone[:fade_samples] *= fade_in
						tone[-fade_samples:] *= fade_out

					if self.output_device is not None:
						sd.play(tone, self.sample_rate, device=self.output_device, blocking=True)
					else:
						sd.play(tone, self.sample_rate, blocking=True)

				print("[Audio] Test beep complete - audio working!")
		except Exception as e:
			from colors import Colors
			print(Colors.red(f"[Audio] Test failed: {e}"))
			self.audio_working = False

	def _play_wav_file(self, sound_name):
		"""
		Play a WAV file from sounds directory

		Args:
			sound_name: Name of sound (key in self.audio_files)
		"""
		import wave

		wav_path = self.audio_files[sound_name]
		if not wav_path.exists():
			return False

		# Read WAV file
		with wave.open(str(wav_path), 'rb') as wav:
			sample_rate = wav.getframerate()
			n_channels = wav.getnchannels()
			frames = wav.readframes(wav.getnframes())
			audio_data = np.frombuffer(frames, dtype=np.int16)

			# Convert to float32 and normalize
			audio_data = audio_data.astype(np.float32) / 32768.0

			# If stereo, convert to mono for JACK (take left channel)
			if n_channels == 2:
				audio_data = audio_data[::2]

			# Apply volume
			audio_data = audio_data * self.volume

		# Play the audio
		if self.use_jack:
			self._play_audio_jack(audio_data, len(audio_data) / sample_rate)
		else:
			import sounddevice as sd
			if self.output_device is not None:
				sd.play(audio_data, sample_rate, device=self.output_device, blocking=True)
			else:
				sd.play(audio_data, sample_rate, blocking=True)

		return True

	def _play_audio_jack(self, audio_data, duration):
		"""
		Play audio data through JACK

		Args:
			audio_data: numpy array of float32 audio samples
			duration: Duration in seconds
		"""
		import jack
		import time

		# Create JACK client
		client = jack.Client("ReaperVC_Audio_Feedback")
		client.outports.register("out_0")

		# Callback to output audio
		self._jack_audio_data = audio_data
		self._jack_position = 0

		@client.set_process_callback
		def process(frames):
			if self._jack_position < len(self._jack_audio_data):
				end_pos = min(self._jack_position + frames, len(self._jack_audio_data))
				chunk = self._jack_audio_data[self._jack_position:end_pos]

				# Pad if needed
				if len(chunk) < frames:
					chunk = np.pad(chunk, (0, frames - len(chunk)))

				client.outports[0].get_array()[:] = chunk
				self._jack_position = end_pos
			else:
				# Silence
				client.outports[0].get_array()[:] = 0

		# Activate and connect to system output
		with client:
			# Connect to system playback
			try:
				client.connect("ReaperVC_Audio_Feedback:out_0", "system:playback_1")
			except:
				pass  # May already be connected or different port names

			# Wait for playback to complete
			time.sleep(duration + 0.1)

		# Clean up
		del self._jack_audio_data
		del self._jack_position

	def _play_tone_jack(self, frequency, duration):
		"""
		Play tone directly through JACK

		Args:
			frequency: Frequency in Hz
			duration: Duration in seconds
		"""
		# Generate tone
		sample_rate = 44100
		num_samples = int(sample_rate * duration)
		t = np.linspace(0, duration, num_samples)
		tone = np.sin(2 * np.pi * frequency * t)

		# Apply fade
		fade_samples = int(0.02 * sample_rate)
		if fade_samples > 0:
			fade_in = np.linspace(0, 1, fade_samples)
			fade_out = np.linspace(1, 0, fade_samples)
			tone[:fade_samples] *= fade_in
			tone[-fade_samples:] *= fade_out

		# Apply volume
		tone = (tone * self.volume).astype(np.float32)

		# Play through JACK
		self._play_audio_jack(tone, duration)

	def play_tone(self, frequency, duration=0.2, fade=0.05):
		"""
		Play a simple tone

		Args:
			frequency: Frequency in Hz
			duration: Duration in seconds
			fade: Fade in/out duration in seconds
		"""
		if not self.audio_working:
			return  # Skip if audio doesn't work

		try:
			if self.use_jack:
				# Use JACK client for direct audio
				self._play_tone_jack(frequency, duration)
			else:
				# Generate tone
				t = np.linspace(0, duration, int(self.sample_rate * duration))
				tone = np.sin(2 * np.pi * frequency * t)

				# Apply fade in/out to prevent clicks
				fade_samples = int(fade * self.sample_rate)
				if fade_samples > 0:
					fade_in = np.linspace(0, 1, fade_samples)
					fade_out = np.linspace(1, 0, fade_samples)

					tone[:fade_samples] *= fade_in
					tone[-fade_samples:] *= fade_out

				# Apply volume
				tone *= self.volume

				# Play to specific device
				if self.output_device is not None:
					sd.play(tone, self.sample_rate, device=self.output_device, blocking=True)
				else:
					# Fallback to default
					sd.play(tone, self.sample_rate, blocking=True)

		except Exception as e:
			from colors import Colors
			print(Colors.red(f"[Audio] Feedback error: {e}"))
			self.audio_working = False  # Disable future attempts

	def play_action_complete(self):
		"""
		Play "action completed" signal
		Uses action-complete.wav if available, otherwise generates quick beep
		"""
		# Try to play custom sound file
		if self.audio_files['action_complete'].exists():
			self._play_wav_file('action_complete')
		else:
			# Fallback to quick beep
			self.play_tone(1000, duration=0.1, fade=0.02)

	def play_completion(self):
		"""
		DEPRECATED: Use play_action_complete() instead
		Kept for backwards compatibility
		"""
		self.play_action_complete()

	def play_error(self):
		"""
		Play error signal
		Low buzzer sound
		"""
		# Single low tone (boop)
		self.play_tone(250, duration=0.15, fade=0.02)

	def play_beep(self):
		"""
		Play simple beep
		"""
		self.play_tone(1000, duration=0.1, fade=0.02)

	def play_shutdown(self):
		"""
		Play shutdown signal
		Uses shutdown.wav if available, otherwise generates descending tone
		"""
		# Try to play custom sound file
		if self.audio_files['shutdown'].exists():
			self._play_wav_file('shutdown')
		else:
			# Fallback to descending tone
			self.play_tone(440, duration=0.3, fade=0.05)

	def play_command_failed(self):
		"""
		Play command failed signal
		Uses command-failed.wav if available, otherwise generates error tone
		"""
		# Try to play custom sound file
		if self.audio_files['command_failed'].exists():
			self._play_wav_file('command_failed')
		else:
			# Fallback to error tone
			self.play_error()

	def speak(self, text):
		"""
		Speak text using TTS (optional, requires pyttsx3)

		Args:
			text: Text to speak
		"""
		try:
			import pyttsx3
			engine = pyttsx3.init()
			engine.setProperty('rate', 180)  # Speed
			engine.setProperty('volume', 0.8)  # Volume
			engine.say(text)
			engine.runAndWait()
		except ImportError:
			print(f"⚠ TTS not available. Message: {text}")
			# Fallback to beep
			self.play_beep()
		except Exception as e:
			print(f"⚠ TTS error: {e}")
			self.play_beep()


if __name__ == "__main__":
	# Test audio feedback
	feedback = AudioFeedback()

	print("Testing audio feedback system...")
	print()

	print("Playing completion signal...")
	feedback.play_completion()
	time.sleep(1)

	print("Playing error signal...")
	feedback.play_error()
	time.sleep(1)

	print("Playing simple beep...")
	feedback.play_beep()
	time.sleep(1)

	print("\nTrying TTS (optional)...")
	feedback.speak("Go ahead")

	print("\nAudio feedback test complete!")
