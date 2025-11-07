"""
Voice Input Module
Main coordinator for voice-based input
Integrates audio capture, VAD, STT, and state filtering
"""

import threading
import yaml
import os
import sys
from queue import Queue

from .audio_capture import AudioCapture
from .vad import VoiceActivityDetector
from .stt_whisper import WhisperSTT
from .transient_detector import TransientDetector

# Import Colors from parent directory
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from colors import Colors


class VoiceInput:
	"""
	Main voice input coordinator
	Handles always-on voice detection and command transcription
	"""

	def __init__(self, config_path="config/voice_config.yaml"):
		"""
		Args:
			config_path: Path to voice configuration file
		"""
		# Load configuration
		with open(config_path, 'r') as f:
			self.config = yaml.safe_load(f)

		# Initialize components
		audio_config = self.config.get('audio', {})
		stt_config = self.config.get('stt', {})
		vad_config = self.config.get('vad', {})
		recording_config = self.config.get('recording_mode', {})

		# Get mic input from environment variable (set by run script)
		import os
		mic_input = int(os.getenv('REAPERVC_MIC_INPUT', '1'))
		input_channel = mic_input - 1  # Convert 1-based to 0-based (input 1 = channel 0)

		print(f"[Mic] Using input: {mic_input} (channel {input_channel})")

		# Audio capture
		self.audio_capture = AudioCapture(
			device_index=audio_config.get('device_index'),
			sample_rate=audio_config.get('sample_rate', 16000),
			frame_duration_ms=audio_config.get('frame_duration_ms', 30),
			input_channel=input_channel
		)

		# Voice Activity Detection
		max_speech_dur = vad_config.get('max_speech_duration', 5.0)
		print(f"[VAD] Initializing with max_speech_duration={max_speech_dur}s")
		self.vad = VoiceActivityDetector(
			sample_rate=audio_config.get('sample_rate', 16000),
			frame_duration_ms=audio_config.get('frame_duration_ms', 30),
			aggressiveness=vad_config.get('aggressiveness', 2),
			max_speech_duration=max_speech_dur
		)

		# Transient Detection (clap/snap for emergency stop)
		transient_config = self.config.get('transient_detection', {})
		self.transient_enabled = transient_config.get('enabled', False)
		if self.transient_enabled:
			self.transient_detector = TransientDetector(
				sample_rate=audio_config.get('sample_rate', 16000),
				threshold_db=transient_config.get('threshold_db', -15),
				cooldown=transient_config.get('cooldown', 1.0)
			)
			print(f"[Transient] Clap/snap detection enabled (threshold={transient_config.get('threshold_db', -15)}dB)")
		else:
			self.transient_detector = None
			print("[Transient] Clap/snap detection disabled")

		# Speech-to-Text
		# Check if GPU is enabled via environment variable (overrides config)
		use_gpu = os.getenv('REAPERVC_USE_GPU', 'false').lower() == 'true'
		if use_gpu:
			print("[GPU] Acceleration enabled for Whisper")

		stt_engine = stt_config.get('engine', 'whisper')
		if stt_engine == 'whisper':
			self.stt = WhisperSTT(
				model_name=stt_config.get('whisper_model', 'base'),
				language=stt_config.get('language', 'en'),
				use_gpu=use_gpu
			)
		else:
			raise ValueError(f"Unsupported STT engine: {stt_engine}")

		# Command queue
		self.command_queue = Queue()

		# Processing thread
		self.is_running = False
		self.processing_thread = None

		# Command callback
		self.command_callback = None
		self.callback_thread = None

		# Telemetry callback
		self.telemetry_callback = None

		# Confidence threshold
		self.confidence_threshold = stt_config.get('confidence_threshold', 0.7)

		# Input gain
		self.input_gain = audio_config.get('input_gain', 1.0)
		if self.input_gain != 1.0:
			print(f"Input gain: {self.input_gain}x ({20*__import__('math').log10(self.input_gain):.1f} dB)")

	def start(self):
		"""Start voice input processing"""
		print("🎙️  Starting voice input system...")

		# Start audio capture
		self.audio_capture.start()

		# Start processing thread
		self.is_running = True
		self.processing_thread = threading.Thread(target=self._process_audio)
		self.processing_thread.daemon = True
		self.processing_thread.start()

		print(Colors.green("[+] Voice input ready (always-on VAD active)"))

	def stop(self):
		"""Stop voice input processing"""
		print("Stopping voice input...")
		self.is_running = False

		# Wait for processing thread to finish
		if self.processing_thread and self.processing_thread.is_alive():
			print("Waiting for processing thread to stop...")
			self.processing_thread.join(timeout=3)
			if self.processing_thread.is_alive():
				print("Warning: Processing thread did not stop cleanly")

		# Stop audio capture
		self.audio_capture.stop()
		print(Colors.green("[+] Voice input stopped"))

	def _process_audio(self):
		"""Main audio processing loop"""
		while self.is_running:
			# Get audio frame from capture
			frame = self.audio_capture.get_frame(timeout=0.5)
			if frame is None:
				continue

			# Apply input gain if configured
			if self.input_gain != 1.0:
				import numpy as np
				frame = (frame.astype(np.float32) * self.input_gain)
				# Clip to prevent overflow
				frame = np.clip(frame, -32768, 32767).astype(np.int16)

			# Check for transient (clap/snap) - emergency stop (if enabled)
			if self.transient_enabled and self.transient_detector.process_frame(frame):
				print(Colors.red("[CLAP/SNAP] Emergency stop detected!"))
				if self.telemetry_callback:
					self.telemetry_callback("Emergency", "Emergency stop detected (clap/snap)")
				# Queue a stop command immediately
				self.command_queue.put({
					'text': 'stop',
					'confidence': 1.0,
					'source': 'transient'
				})

			# Process through VAD
			speech_ended, audio_data = self.vad.process_frame(frame)

			if speech_ended:
				# Speech utterance complete - transcribe
				self._transcribe_and_queue(audio_data)

	def _transcribe_and_queue(self, audio_data):
		"""
		Transcribe audio and add to command queue

		Args:
			audio_data: numpy array of audio samples
		"""
		# Full STT transcription
		result = self.stt.transcribe(audio_data, sample_rate=self.audio_capture.sample_rate)
		text = result.get('text', '').strip()
		confidence = result.get('confidence', 0.0)

		if not text:
			print("[no speech detected]")
			return

		# Show transcription with color
		if confidence >= self.confidence_threshold:
			print(Colors.green(f"[OK] '{text}' (conf={confidence:.2f})"))
			if self.telemetry_callback:
				self.telemetry_callback("Heard", f"[OK] '{text}' (conf={confidence:.2f})")
		else:
			print(Colors.yellow(f"[?] '{text}' (conf={confidence:.2f})"))
			if self.telemetry_callback:
				self.telemetry_callback("Heard", f"[?] '{text}' (conf={confidence:.2f}) - Low confidence")

		# Filter out very low confidence transcriptions (likely noise/phantom detections)
		MIN_CONFIDENCE = 0.3  # Reject anything below 30% confidence
		if confidence < MIN_CONFIDENCE:
			print(Colors.red(f"[Filtered] Confidence too low ({confidence:.2f} < {MIN_CONFIDENCE}), ignoring"))
			if self.telemetry_callback:
				self.telemetry_callback("Heard", f"Filtered: Confidence too low ({confidence:.2f}), ignoring")
			return

		# Add to command queue
		self.command_queue.put({
			'text': text,
			'confidence': confidence,
			'method': 'whisper'
		})

	def get_command(self, timeout=None):
		"""
		Get next command from queue

		Args:
			timeout: Timeout in seconds (None = blocking)

		Returns:
			dict: Command info or None
		"""
		try:
			return self.command_queue.get(timeout=timeout)
		except:
			return None

	def set_command_callback(self, callback):
		"""
		Set callback function for commands

		Args:
			callback: Function to call with command text
		"""
		self.command_callback = callback

		# Start callback thread
		import threading
		def process_commands():
			while self.is_running:
				cmd = self.get_command(timeout=0.5)
				if cmd and self.command_callback:
					self.command_callback(cmd['text'])

		self.callback_thread = threading.Thread(target=process_commands)
		self.callback_thread.daemon = True
		self.callback_thread.start()

	def set_telemetry_callback(self, callback):
		"""
		Set callback function for telemetry logging

		Args:
			callback: Function to call with (category, message)
		"""
		self.telemetry_callback = callback


if __name__ == "__main__":
	# Simple test
	print("Voice Input Module Test")
	print("This requires audio hardware and Whisper model")

	try:
		voice = VoiceInput()
		voice.start()

		print("\nListening... Speak into your microphone")
		print("Press Ctrl+C to exit\n")

		import time
		while True:
			cmd = voice.get_command(timeout=1)
			if cmd:
				print(f"→ Command received: {cmd}")
			time.sleep(0.1)

	except KeyboardInterrupt:
		print("\nExiting...")
		voice.stop()
	except Exception as e:
		print(f"Error: {e}")
