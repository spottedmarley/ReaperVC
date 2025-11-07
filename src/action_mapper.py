"""
Action Name Mapper
Maps Reaper action names to action IDs by parsing reaper-actions.txt
This makes command configurations portable across different Reaper installations
"""

from pathlib import Path


class ActionMapper:
	"""
	Parses reaper-actions.txt and provides mapping between action names and IDs
	"""

	def __init__(self, reaper_actions_file):
		"""
		Initialize the action mapper

		Args:
			reaper_actions_file: Path to reaper-actions.txt file
		"""
		self.action_map = {}
		self._parse_actions_file(reaper_actions_file)

	def _parse_actions_file(self, filepath):
		"""
		Parse reaper-actions.txt file

		Expected format:
		Main	1013	Transport: Record
		Main	40026	File: Save project
		etc.
		"""
		filepath = Path(filepath)
		if not filepath.exists():
			raise FileNotFoundError(
				f"reaper-actions.txt not found at {filepath}\n"
				"Please run 'SWS/S&M: Dump action list (all actions)' in Reaper\n"
				"and save the output as reaper-actions.txt in the project root."
			)

		with open(filepath, 'r', encoding='utf-8') as f:
			for line in f:
				line = line.strip()
				if not line:
					continue

				# Parse tab-separated format: Section\tID\tName
				parts = line.split('\t')
				if len(parts) < 3:
					continue

				section = parts[0]
				action_id_str = parts[1]
				action_name = parts[2]

				# Action ID can be either an integer or a string (for SWS extensions)
				try:
					action_id = int(action_id_str)
				except ValueError:
					# Keep as string for SWS actions like "_S&M_INS_MARKER_EDIT"
					action_id = action_id_str

				# Store in map - prioritize Main section (don't overwrite Main with other sections)
				if action_name not in self.action_map or section == "Main":
					self.action_map[action_name] = action_id

		print(f"[ActionMapper] Loaded {len(self.action_map)} actions from {filepath.name}")

	def get_action_id(self, action_name):
		"""
		Get action ID for a given action name

		Args:
			action_name: Action name (e.g., "Transport: Record")

		Returns:
			int: Action ID or None if not found
		"""
		return self.action_map.get(action_name)

	def resolve_action(self, action_spec):
		"""
		Resolve an action specification to an action ID

		Args:
			action_spec: Either an int (action ID) or str (action name)

		Returns:
			int or str: Action ID (int for numeric IDs, str for SWS command IDs)

		Raises:
			ValueError: If action name not found in map
		"""
		# If already an int, return it
		if isinstance(action_spec, int):
			return action_spec

		# If string, check if it's already an action ID (like "_S&M_INS_MARKER_EDIT")
		if isinstance(action_spec, str):
			# Check if it's an action name that needs to be looked up
			action_id = self.get_action_id(action_spec)
			if action_id is None:
				raise ValueError(
					f"Action '{action_spec}' not found in reaper-actions.txt\n"
					f"Make sure the action name exactly matches the output from Reaper."
				)
			return action_id

		raise TypeError(f"Invalid action spec type: {type(action_spec)}")

	def resolve_actions(self, action_specs):
		"""
		Resolve a list of action specifications

		Args:
			action_specs: List of action IDs or names

		Returns:
			list: List of action IDs
		"""
		return [self.resolve_action(spec) for spec in action_specs]


if __name__ == "__main__":
	# Test the mapper
	print("Action Mapper Test\n")

	mapper = ActionMapper("../reaper-actions.txt")

	test_actions = [
		"Transport: Record",
		"Transport: Play",
		"Transport: Stop",
		"File: Save project",
		"Edit: Undo",
	]

	print("\nTesting action resolution:")
	for action_name in test_actions:
		action_id = mapper.get_action_id(action_name)
		if action_id:
			print(f"  ✓ {action_name} → {action_id}")
		else:
			print(f"  ✗ {action_name} → NOT FOUND")
