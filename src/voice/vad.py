"""
Voice Activity Detection Module
Detects when user is speaking vs silence
"""

import webrtcvad
import collections
import numpy as np
import time


class VoiceActivityDetector:
	"""
	Detects voice activity in audio stream using WebRTC VAD
	Buffers audio and triggers on speech detection
	"""

	def __init__(self, sample_rate=16000, frame_duration_ms=30, aggressiveness=2, max_speech_duration=5.0):
		"""
		Args:
			sample_rate: Audio sample rate (must be 8000, 16000, 32000, or 48000)
			frame_duration_ms: Frame duration (must be 10, 20, or 30 ms)
			aggressiveness: VAD aggressiveness (0-3, higher = more aggressive)
			max_speech_duration: Maximum speech duration in seconds before forcing end
		"""
		self.sample_rate = sample_rate
		self.frame_duration_ms = frame_duration_ms
		self.aggressiveness = aggressiveness
		self.max_speech_duration = max_speech_duration

		# Create VAD instance
		self.vad = webrtcvad.Vad(aggressiveness)

		# Speech detection state
		self.is_speaking = False
		self.speech_frames = []
		self.speech_start_time = None

		# Ring buffer for pre-speech audio (to capture start of utterance)
		self.ring_buffer = collections.deque(maxlen=10)

		# Counters for triggering/un-triggering
		self.num_voiced = 0
		self.num_unvoiced = 0

		# Thresholds (number of frames)
		self.trigger_threshold = 8  # Start of speech
		self.untrigger_threshold = 20  # End of speech

	def process_frame(self, audio_frame):
		"""
		Process single audio frame

		Args:
			audio_frame: numpy array of int16 audio samples

		Returns:
			tuple: (is_speech, audio_data)
				is_speech: True if speech detected in this frame
				audio_data: Complete utterance if speech ended, None otherwise
		"""
		# Convert numpy array to bytes
		audio_bytes = audio_frame.tobytes()

		# Check if frame contains speech
		is_speech = self.vad.is_speech(audio_bytes, self.sample_rate)

		# State machine for speech detection
		if not self.is_speaking:
			# Not currently in speech
			self.ring_buffer.append((audio_frame, is_speech))

			if is_speech:
				self.num_voiced += 1
			else:
				self.num_voiced = 0

			# Trigger speech detection
			if self.num_voiced > self.trigger_threshold:
				self.is_speaking = True
				self.speech_frames = list(self.ring_buffer)
				self.speech_start_time = time.time()
				self.ring_buffer.clear()
				# Suppress speech started message

			return False, None

		else:
			# Currently in speech
			self.speech_frames.append((audio_frame, is_speech))

			if not is_speech:
				self.num_unvoiced += 1
			else:
				self.num_unvoiced = 0

			# Check if max speech duration exceeded
			speech_duration = time.time() - self.speech_start_time if self.speech_start_time else 0
			force_end = speech_duration > self.max_speech_duration

			# End speech detection (either by silence or timeout)
			if self.num_unvoiced > self.untrigger_threshold or force_end:
				self.is_speaking = False
				self.num_voiced = 0
				self.num_unvoiced = 0
				self.speech_start_time = None

				# Extract audio data
				audio_data = np.concatenate([frame for frame, _ in self.speech_frames])
				self.speech_frames = []

				# Debug output
				if force_end:
					print(f"[VAD] Signal FORCED after {speech_duration:.1f}s (max: {self.max_speech_duration}s)")
				else:
					print(f"[VAD] Signal ended naturally after {speech_duration:.1f}s (silence detected)")
				return True, audio_data

			return False, None

	def reset(self):
		"""Reset VAD state"""
		self.is_speaking = False
		self.speech_frames = []
		self.speech_start_time = None
		self.ring_buffer.clear()
		self.num_voiced = 0
		self.num_unvoiced = 0


if __name__ == "__main__":
	# Simple test
	vad = VoiceActivityDetector()
	print(f"VAD initialized (aggressiveness={vad.aggressiveness})")
