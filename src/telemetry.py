"""
Telemetry Logger
Captures all debug and diagnostic output for troubleshooting
Logs are written to /extras/telemetry.md on app shutdown
Live telemetry written to /tmp/reapervc_telemetry.log
"""

import datetime
from pathlib import Path


class Telemetry:
	"""
	Singleton telemetry logger
	Captures all diagnostic information during runtime
	"""
	_instance = None
	_logs = []
	_session_start = None
	_live_log_file = "/tmp/reapervc_telemetry.log"

	def __new__(cls):
		if cls._instance is None:
			cls._instance = super(Telemetry, cls).__new__(cls)
			cls._logs = []
			cls._session_start = datetime.datetime.now()
			# Clear/create live log file
			try:
				with open(cls._live_log_file, 'w') as f:
					f.write(f"=== ReaperVC Telemetry - {cls._session_start.strftime('%Y-%m-%d %H:%M:%S')} ===\n\n")
			except Exception:
				pass
		return cls._instance

	@classmethod
	def log(cls, category, message):
		"""
		Log a telemetry event

		Args:
			category: Category of log (e.g., "OSC", "Claude", "State", "Command")
			message: Log message
		"""
		timestamp = datetime.datetime.now()
		elapsed = (timestamp - cls._session_start).total_seconds()
		entry = {
			"timestamp": timestamp,
			"elapsed": elapsed,
			"category": category,
			"message": message
		}
		cls._logs.append(entry)

		# Write live telemetry to file for real-time monitoring
		try:
			timestamp_str = timestamp.strftime('%H:%M:%S')
			# Clean message for single-line display
			clean_msg = message.replace('\n', ' ').strip()
			console_msg = f"[{timestamp_str}] [{category:8}] {clean_msg}\n"

			with open(cls._live_log_file, 'a') as f:
				f.write(console_msg)
				f.flush()  # Force immediate write to disk
		except Exception:
			pass

	@classmethod
	def write_to_file(cls, filepath):
		"""
		Write all telemetry logs to markdown file

		Args:
			filepath: Path to telemetry.md file
		"""
		with open(filepath, 'w') as f:
			f.write("# ReaperVC Telemetry Log\n\n")
			f.write(f"**Session Start:** {cls._session_start.strftime('%Y-%m-%d %H:%M:%S')}\n")
			f.write(f"**Session Duration:** {(datetime.datetime.now() - cls._session_start).total_seconds():.2f}s\n")
			f.write(f"**Total Events:** {len(cls._logs)}\n\n")
			f.write("---\n\n")

			# Group by category
			categories = {}
			for entry in cls._logs:
				cat = entry['category']
				if cat not in categories:
					categories[cat] = []
				categories[cat].append(entry)

			# Write logs by category
			for cat in sorted(categories.keys()):
				f.write(f"## {cat}\n\n")
				for entry in categories[cat]:
					timestamp_str = entry['timestamp'].strftime('%H:%M:%S.%f')[:-3]
					f.write(f"**[{timestamp_str}] ({entry['elapsed']:.3f}s)**\n")
					f.write(f"```\n{entry['message']}\n```\n\n")

			# Write chronological log
			f.write("---\n\n")
			f.write("## Chronological Log\n\n")
			for entry in cls._logs:
				timestamp_str = entry['timestamp'].strftime('%H:%M:%S.%f')[:-3]
				f.write(f"**[{timestamp_str}] {entry['category']}** ({entry['elapsed']:.3f}s)\n")
				f.write(f"```\n{entry['message']}\n```\n\n")

	@classmethod
	def clear(cls):
		"""Clear all logs (called on app start)"""
		cls._logs = []
		cls._session_start = datetime.datetime.now()


# Global convenience function
def log(category, message):
	"""
	Global telemetry logging function

	Args:
		category: Category of log
		message: Log message
	"""
	Telemetry.log(category, message)
