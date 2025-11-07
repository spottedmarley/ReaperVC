"""
Audio Capture Module
Handles continuous microphone input
"""

import pyaudio
import numpy as np
from queue import Queue
import threading
import os


class AudioCapture:
	"""
	Captures audio from microphone continuously
	Provides audio frames to VAD and STT modules
	"""

	def __init__(self, device_index=None, sample_rate=16000, frame_duration_ms=30, input_channel=0):
		self.device_index = device_index
		self.sample_rate = sample_rate
		self.frame_duration_ms = frame_duration_ms
		self.input_channel = input_channel  # 0 = input 1, 1 = input 2

		# Calculate frame size in samples
		self.frame_size = int(sample_rate * frame_duration_ms / 1000)

		# Audio queue for processing
		self.audio_queue = Queue()

		# Set JACK client name before creating PyAudio
		os.environ['JACK_CLIENT_NAME'] = 'ReaperVC'

		# PyAudio setup
		self.audio = pyaudio.PyAudio()
		self.stream = None
		self.is_running = False
		self.capture_thread = None

	def _audio_callback(self, in_data, frame_count, time_info, status):
		"""PyAudio callback for audio frames"""
		if status:
			print(f"Audio status: {status}")

		# Convert bytes to numpy array (stereo)
		audio_frame = np.frombuffer(in_data, dtype=np.int16)

		# Reshape to (samples, channels) and extract the desired channel
		try:
			audio_frame = audio_frame.reshape(-1, 2)[:, self.input_channel]
		except ValueError as e:
			# If reshape fails, we might be getting mono data
			print(f"Warning: Reshape failed (expected stereo): {e}")
			# Just use the mono data as-is
			pass

		self.audio_queue.put(audio_frame)

		return (in_data, pyaudio.paContinue)

	def start(self):
		"""Start capturing audio"""
		print(f"Starting audio capture (device={self.device_index}, rate={self.sample_rate}Hz, channel={self.input_channel + 1})")

		self.stream = self.audio.open(
			format=pyaudio.paInt16,
			channels=2,  # Open stereo to access both inputs
			rate=self.sample_rate,
			input=True,
			input_device_index=self.device_index,
			frames_per_buffer=self.frame_size,
			stream_callback=self._audio_callback
		)

		self.is_running = True
		self.stream.start_stream()

	def stop(self):
		"""Stop capturing audio"""
		self.is_running = False

		try:
			if self.stream:
				if self.stream.is_active():
					self.stream.stop_stream()
				self.stream.close()
				self.stream = None
		except Exception as e:
			print(f"Warning: Error stopping audio stream: {e}")

		try:
			self.audio.terminate()
		except Exception as e:
			print(f"Warning: Error terminating PyAudio: {e}")

		print("Audio capture stopped")

	def get_frame(self, timeout=1):
		"""
		Get next audio frame from queue

		Args:
			timeout: Timeout in seconds

		Returns:
			numpy.ndarray: Audio frame or None if timeout
		"""
		try:
			return self.audio_queue.get(timeout=timeout)
		except:
			return None

	def list_devices(self):
		"""List all available audio devices"""
		info = self.audio.get_host_api_info_by_index(0)
		num_devices = info.get('deviceCount')

		print(f"\nAvailable audio devices:")
		for i in range(num_devices):
			device_info = self.audio.get_device_info_by_host_api_device_index(0, i)
			if device_info.get('maxInputChannels') > 0:
				print(f"  [{i}] {device_info.get('name')}")


if __name__ == "__main__":
	# Test audio capture
	capture = AudioCapture()
	capture.list_devices()

	print("\nStarting capture for 5 seconds...")
	capture.start()

	import time
	time.sleep(5)

	capture.stop()
