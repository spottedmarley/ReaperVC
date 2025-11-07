"""
Number Extraction Utility
Converts spoken numbers to digits for voice commands
"""

import re


class NumberExtractor:
	"""
	Extract and convert spoken numbers from text
	Handles both spelled-out and digit forms
	"""

	def __init__(self):
		# Try to import word2number, but provide fallback
		try:
			from word2number import w2n
			self.w2n = w2n
			self.has_w2n = True
		except ImportError:
			self.w2n = None
			self.has_w2n = False
			print("[NumberExtractor] word2number not installed, using basic extraction")

	def extract_time(self, text):
		"""
		Extract time value from text (supports minutes and seconds)

		Args:
			text: Voice command text (e.g., "go to one minute thirty seconds")

		Returns:
			float: Time in seconds, or None if not found/invalid
		"""
		# Normalize text
		text = text.lower().strip()

		# Remove command phrases to isolate the time
		for phrase in ['cursor to', 'playhead to', 'go to', 'move cursor to', 'move playhead to']:
			text = text.replace(phrase, '').strip()

		# Try to extract time components
		minutes = 0
		seconds = 0

		# Check for explicit "minute(s)" and "second(s)" keywords
		import re

		# Pattern: "X minute(s) Y second(s)" or "X minute(s)" or "Y second(s)"
		# Also handle "X minute(s) Y" (without "second" keyword)
		minute_match = re.search(r'(\w+\s+\w+|\w+)\s+minute', text)
		second_match = re.search(r'(\w+\s+\w+|\w+)\s+second', text)

		# Also check for implicit seconds after minutes: "two minutes thirty" = 2:30
		if minute_match and not second_match:
			# Check if there's a number after "minute(s)"
			remaining_text = text[minute_match.end():]
			# Remove 's' from "minutes" if present
			remaining_text = remaining_text.replace('s', '').strip()
			# Try to extract a number from what's left
			if remaining_text:
				implicit_seconds = self._extract_number(remaining_text)
				if implicit_seconds:
					seconds = implicit_seconds

		if minute_match:
			minute_text = minute_match.group(1).strip()
			minutes = self._extract_number(minute_text)

		if second_match:
			second_text = second_match.group(1).strip()
			seconds = self._extract_number(second_text)

		# If we found time components, return total seconds
		if minutes or seconds:
			total = (minutes * 60) + seconds
			return float(total) if total > 0 else None

		# Fallback: check if it's just a number (assume seconds)
		number = self._extract_number(text)
		if number:
			return float(number)

		print(f"[NumberExtractor] Could not extract time from: '{text}'")
		return None

	def _extract_number(self, text):
		"""
		Extract a number from text (helper for time parsing)

		Args:
			text: Text containing a number

		Returns:
			int: Extracted number, or 0 if not found
		"""
		# Try digit form first
		import re
		digit_match = re.search(r'\b(\d+)\b', text)
		if digit_match:
			return int(digit_match.group(1))

		# Try word2number if available
		if self.has_w2n:
			# Try custom parser first
			result = self._parse_spoken_number(text)
			if result:
				return result

			# Try w2n
			try:
				return self.w2n.word_to_num(text)
			except ValueError:
				pass

		# Fallback: basic parser
		result = self._parse_spoken_number(text)
		return result if result else 0

	def extract_bpm(self, text, min_bpm=40, max_bpm=960):
		"""
		Extract BPM value from text

		Args:
			text: Voice command text (e.g., "set tempo to one twenty")
			min_bpm: Minimum valid BPM (Reaper limit: 40)
			max_bpm: Maximum valid BPM (Reaper limit: 960)

		Returns:
			int: BPM value, or None if not found/invalid
		"""
		# Normalize text
		text = text.lower().strip()

		# Remove command phrases to isolate the number
		for phrase in ['set tempo to', 'set the tempo to', 'set temp to', 'tempo']:
			text = text.replace(phrase, '').strip()

		# Try to extract number using different methods
		bpm = None

		# Method 1: Check for digits already in text (e.g., "120")
		digit_match = re.search(r'\b(\d+)\b', text)
		if digit_match:
			bpm = int(digit_match.group(1))

		# Method 2: Try custom parser first (better for tempo patterns like "one twenty")
		elif self.has_w2n:
			# Try custom parser first (handles "one twenty" = 120 better)
			bpm = self._parse_spoken_number(text)

			# If that didn't work, try word2number
			if bpm is None:
				try:
					bpm = self.w2n.word_to_num(text)
				except ValueError:
					bpm = None

		# Method 3: Fallback basic parsing
		else:
			bpm = self._parse_spoken_number(text)

		# Validate range
		if bpm is not None:
			if min_bpm <= bpm <= max_bpm:
				return bpm
			else:
				print(f"[NumberExtractor] BPM {bpm} out of range ({min_bpm}-{max_bpm})")
				return None

		print(f"[NumberExtractor] Could not extract valid BPM from: '{text}'")
		return None

	def extract_pan_percentage(self, text):
		"""
		Extract pan percentage from text

		Args:
			text: Voice command text (e.g., "pan left 30" or "pan right fifty percent")

		Returns:
			int: Percentage value (0-100), defaults to 50 if no number found
		"""
		# Normalize text
		text = text.lower().strip()

		# Remove command phrases to isolate the number
		for phrase in ['pan left', 'pan right', 'left pan', 'right pan', 'track left', 'track right', 'percent', '%']:
			text = text.replace(phrase, '').strip()

		# Try to extract number
		percentage = None

		# Method 1: Check for digits (e.g., "30", "50")
		digit_match = re.search(r'\b(\d+)\b', text)
		if digit_match:
			percentage = int(digit_match.group(1))
		# Method 2: Try to extract spoken number
		else:
			percentage = self._extract_number(text)

		# _extract_number returns 0 when no number is found, treat as None
		if percentage == 0 and not text.strip():
			percentage = None

		# Validate range (0-100 for percentage)
		if percentage is not None:
			if 0 <= percentage <= 100:
				return percentage
			else:
				print(f"[NumberExtractor] Percentage {percentage} out of range (0-100)")
				return 50  # Default to 50% if invalid

		# No number found - default to 50%
		return 50

	def _parse_spoken_number(self, text):
		"""
		Basic parsing for common spoken tempo numbers
		Handles patterns like "one twenty" (120), "ninety" (90), etc.
		"""
		# Common tempo words
		word_map = {
			# Singles
			'zero': 0, 'one': 1, 'two': 2, 'three': 3, 'four': 4,
			'five': 5, 'six': 6, 'seven': 7, 'eight': 8, 'nine': 9,
			# Tens
			'ten': 10, 'eleven': 11, 'twelve': 12, 'thirteen': 13,
			'fourteen': 14, 'fifteen': 15, 'sixteen': 16, 'seventeen': 17,
			'eighteen': 18, 'nineteen': 19, 'twenty': 20, 'thirty': 30,
			'forty': 40, 'fifty': 50, 'sixty': 60, 'seventy': 70,
			'eighty': 80, 'ninety': 90,
			# Hundreds
			'hundred': 100, 'thousand': 1000
		}

		words = text.split()
		total = 0
		current = 0

		for word in words:
			word = word.strip()
			if word in word_map:
				value = word_map[word]

				if value >= 100:
					# Multiplier (e.g., "one hundred")
					current = current * value if current else value
				else:
					# Add to current (e.g., "twenty five" = 25)
					current += value
			elif word == 'and':
				# Ignore "and" in numbers
				continue

		total = current

		# Special handling for common tempo patterns
		# "one twenty" (120), "one thirty" (130), etc.
		if len(words) == 2:
			first = words[0].strip()
			second = words[1].strip()

			if first in ['one', 'two', 'three'] and second in word_map:
				second_val = word_map[second]
				if 20 <= second_val <= 90:
					# "one twenty" = 120
					total = (word_map[first] * 100) + second_val

		return total if total > 0 else None


if __name__ == "__main__":
	# Test cases
	extractor = NumberExtractor()

	test_cases = [
		"set tempo to one twenty",
		"set the tempo to 120",
		"tempo ninety",
		"set temp 140",
		"one hundred sixty",
		"sixty five",
		"tempo to forty",
		"nine hundred fifty nine",
		"tempo 30",  # Below min (should fail)
		"tempo 1000",  # Above max (should fail)
	]

	print("Testing NumberExtractor:\n")
	for test in test_cases:
		result = extractor.extract_bpm(test)
		print(f"  '{test}' → {result}")
