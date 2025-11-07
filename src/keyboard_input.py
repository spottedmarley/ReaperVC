"""
Keyboard Input Module
Simulates keyboard input for typing text into Reaper track names, etc.
"""

import subprocess
import time
from typing import Optional


class KeyboardInput:
	"""
	Handles keyboard input simulation using xdotool (Linux)
	"""

	def __init__(self):
		"""Initialize the keyboard input handler"""
		# Check if xdotool is available
		try:
			result = subprocess.run(
				['which', 'xdotool'],
				capture_output=True,
				text=True,
				timeout=1
			)
			self.available = result.returncode == 0
			if not self.available:
				print("[Warning] xdotool not found - keyboard input disabled")
		except Exception as e:
			print(f"[Warning] Could not check for xdotool: {e}")
			self.available = False

	def type_text(self, text: str, delay: float = 0.1) -> bool:
		"""
		Type text as if typed on keyboard

		Args:
			text: Text to type
			delay: Delay in seconds before typing (to allow focus)

		Returns:
			bool: True if successful, False otherwise
		"""
		if not self.available:
			print("[Keyboard] xdotool not available")
			return False

		if not text:
			return True

		try:
			# Small delay to allow window/field to focus
			if delay > 0:
				time.sleep(delay)

			# Use xdotool to type the text directly
			# Don't try to change window focus - let it type wherever focus already is
			# --clearmodifiers ensures clean state
			# type command simulates actual keystrokes
			result = subprocess.run(
				['xdotool', 'type', '--clearmodifiers', '--', text],
				capture_output=True,
				text=True,
				timeout=5
			)

			if result.returncode != 0:
				print(f"[Keyboard] Error typing text: {result.stderr}")
				print(f"[Keyboard] Return code: {result.returncode}")
				print(f"[Keyboard] Stdout: {result.stdout}")
				return False

			print(f"[Keyboard] xdotool succeeded (return code: {result.returncode})")
			return True

		except subprocess.TimeoutExpired:
			print("[Keyboard] Timeout while typing text")
			return False
		except Exception as e:
			print(f"[Keyboard] Error: {e}")
			return False

	def press_key(self, key: str, delay: float = 0.1) -> bool:
		"""
		Press a single key (like Enter, Tab, Escape, etc.)

		Args:
			key: Key name (Return, Tab, Escape, etc.)
			delay: Delay in seconds before pressing

		Returns:
			bool: True if successful, False otherwise
		"""
		if not self.available:
			print("[Keyboard] xdotool not available")
			return False

		try:
			if delay > 0:
				time.sleep(delay)

			result = subprocess.run(
				['xdotool', 'key', '--clearmodifiers', key],
				capture_output=True,
				text=True,
				timeout=5
			)

			if result.returncode != 0:
				print(f"[Keyboard] Error pressing key: {result.stderr}")
				return False

			return True

		except subprocess.TimeoutExpired:
			print("[Keyboard] Timeout while pressing key")
			return False
		except Exception as e:
			print(f"[Keyboard] Error: {e}")
			return False

	def type_and_enter(self, text: str, delay: float = 0.1) -> bool:
		"""
		Type text and press Enter

		Args:
			text: Text to type
			delay: Delay in seconds before typing

		Returns:
			bool: True if successful, False otherwise
		"""
		if self.type_text(text, delay):
			time.sleep(0.05)  # Small delay between typing and Enter
			return self.press_key('Return', delay=0)
		return False


if __name__ == "__main__":
	# Test the keyboard input
	print("Keyboard Input Test\n")

	kb = KeyboardInput()

	if kb.available:
		print("✓ xdotool is available")
		print("\nTest 1: Type 'Hello World' in 3 seconds...")
		time.sleep(3)
		kb.type_text("Hello World")
		print("✓ Text typed")

		print("\nTest 2: Press Enter in 2 seconds...")
		time.sleep(2)
		kb.press_key('Return')
		print("✓ Enter pressed")
	else:
		print("✗ xdotool not available")
		print("Install with: sudo apt-get install xdotool")
