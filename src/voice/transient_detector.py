"""
Transient Detector
Detects sharp transients like claps and finger snaps
"""

import numpy as np


class TransientDetector:
	"""
	Detects sharp transients (claps, snaps) in audio
	Uses amplitude envelope and short-term energy
	"""

	def __init__(self, sample_rate=48000, threshold_db=-20, cooldown=0.5):
		"""
		Args:
			sample_rate: Audio sample rate
			threshold_db: Threshold in dB for transient detection
			cooldown: Minimum time between detections (seconds)
		"""
		self.sample_rate = sample_rate
		self.threshold_db = threshold_db
		self.threshold_amplitude = 10 ** (threshold_db / 20)  # Convert dB to linear
		self.cooldown = cooldown
		self.last_detection_time = 0

		# Buffer for tracking recent energy
		self.buffer_size = int(sample_rate * 0.05)  # 50ms buffer
		self.energy_history = []

	def process_frame(self, audio_frame):
		"""
		Process audio frame and detect transients

		Args:
			audio_frame: numpy array of int16 audio samples

		Returns:
			bool: True if transient detected
		"""
		import time

		# Check cooldown
		current_time = time.time()
		if current_time - self.last_detection_time < self.cooldown:
			return False

		# Convert to float and normalize
		audio_float = audio_frame.astype(np.float32) / 32768.0

		# Calculate RMS energy of this frame
		rms = np.sqrt(np.mean(audio_float ** 2))

		# Calculate peak amplitude
		peak = np.max(np.abs(audio_float))

		# Transient detection criteria:
		# 1. Peak amplitude above threshold
		# 2. High peak-to-RMS ratio (indicates sharp attack)
		# 3. Sudden increase from recent history

		if peak < self.threshold_amplitude:
			# Too quiet
			self.energy_history.append(rms)
			if len(self.energy_history) > 10:
				self.energy_history.pop(0)
			return False

		# Check peak-to-RMS ratio (transients have high ratio)
		if rms > 0:
			peak_to_rms = peak / rms
		else:
			peak_to_rms = 0

		# Claps/snaps typically have peak-to-RMS > 3
		if peak_to_rms < 3.0:
			self.energy_history.append(rms)
			if len(self.energy_history) > 10:
				self.energy_history.pop(0)
			return False

		# Check if this is sudden compared to recent history
		if self.energy_history:
			avg_recent = np.mean(self.energy_history)
			# Current peak should be at least 5x louder than recent average
			if peak < avg_recent * 5:
				self.energy_history.append(rms)
				if len(self.energy_history) > 10:
					self.energy_history.pop(0)
				return False

		# Transient detected!
		self.last_detection_time = current_time
		self.energy_history = []  # Reset history after detection
		return True

	def reset(self):
		"""Reset detector state"""
		self.energy_history = []
		self.last_detection_time = 0
