"""
Whisper Speech-to-Text Module
Converts speech audio to text using OpenAI Whisper
"""

import whisper
import numpy as np
import tempfile
import soundfile as sf


class WhisperSTT:
	"""
	Speech-to-text using OpenAI Whisper
	Supports multiple model sizes for accuracy/speed tradeoff
	"""

	def __init__(self, model_name="base", language="en", use_gpu=False):
		"""
		Args:
			model_name: Whisper model size (tiny, base, small, medium, large)
			language: Language code (en, es, fr, etc.)
			use_gpu: Use GPU if available (requires CUDA/ROCm)
		"""
		self.model_name = model_name
		self.language = language
		self.use_gpu = use_gpu

		print(f"Loading Whisper model '{model_name}'...")
		self.model = whisper.load_model(model_name)
		print("Whisper model loaded")

	def transcribe(self, audio_data, sample_rate=16000):
		"""
		Transcribe audio to text

		Args:
			audio_data: numpy array of int16 audio samples
			sample_rate: Sample rate of audio

		Returns:
			dict: {
				'text': transcribed text,
				'confidence': confidence score (0-1),
				'language': detected language
			}
		"""
		try:
			# Convert int16 to float32 normalized to [-1, 1]
			audio_float = audio_data.astype(np.float32) / 32768.0

			# Whisper expects 16kHz audio
			if sample_rate != 16000:
				# High-quality resampling using scipy resample_poly (polyphase filtering)
				# More accurate than simple resample, especially for 48kHz -> 16kHz (3:1 ratio)
				import scipy.signal
				from fractions import Fraction

				# Calculate decimation ratio
				ratio = Fraction(16000, sample_rate)
				up = ratio.numerator
				down = ratio.denominator

				# Use polyphase resampling for better quality
				audio_float = scipy.signal.resample_poly(audio_float, up, down)

			# Transcribe
			result = self.model.transcribe(
				audio_float,
				language=self.language,
				task="transcribe",
				fp16=False  # Set to True for GPU
			)

			# Extract confidence (average of segment probabilities)
			segments = result.get('segments', [])
			if segments:
				confidence = np.mean([s.get('no_speech_prob', 0.5) for s in segments])
				confidence = 1.0 - confidence  # Invert no_speech_prob
			else:
				confidence = 0.5

			return {
				'text': result['text'].strip(),
				'confidence': confidence,
				'language': result.get('language', self.language)
			}

		except Exception as e:
			print(f"Whisper transcription error: {e}")
			return {
				'text': "",
				'confidence': 0.0,
				'language': self.language,
				'error': str(e)
			}


if __name__ == "__main__":
	# Simple test
	print("Testing Whisper STT...")
	stt = WhisperSTT(model_name="tiny")  # Use tiny for quick test

	# Generate test audio (silence)
	test_audio = np.zeros(16000, dtype=np.int16)  # 1 second of silence
	result = stt.transcribe(test_audio)
	print(f"Result: {result}")
