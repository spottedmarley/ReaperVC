#!/usr/bin/env python3
"""
Command List GUI - Display all ReaperVC commands organized by group
"""

import tkinter as tk
from tkinter import ttk
import yaml
from pathlib import Path
import threading


class CommandListWindow:
	"""
	Display a window showing all voice commands organized by group
	"""

	def __init__(self, commands_config):
		"""
		Initialize command list window

		Args:
			commands_config: Loaded commands dictionary from YAML
		"""
		self.commands_config = commands_config
		self.window = None
		self.is_visible = False

	def _organize_by_group(self):
		"""
		Organize commands by group name

		Returns:
			dict: {group_name: [(command_name, patterns), ...]}
		"""
		groups = {}

		for cmd_name, cmd_config in self.commands_config['commands'].items():
			group = cmd_config.get('group', 'Uncategorized')

			if group not in groups:
				groups[group] = []

			patterns = cmd_config.get('patterns', [])
			groups[group].append((cmd_name, patterns))

		# Sort commands within each group
		for group in groups:
			groups[group] = sorted(groups[group], key=lambda x: x[0])

		# Sort groups by total number of patterns (ascending)
		sorted_groups = {}
		for group in sorted(groups.keys(), key=lambda g: sum(len(patterns) for _, patterns in groups[g])):
			sorted_groups[group] = groups[group]

		return sorted_groups

	def show(self):
		"""Create and display the command list window"""
		if self.is_visible and self.window:
			# Window already open, just raise it
			self.window.lift()
			self.window.focus_force()
			return

		self.is_visible = True
		self._create_window()

	def hide(self):
		"""Hide the command list window"""
		if self.window:
			self.window.withdraw()
			self.is_visible = False

	def toggle(self):
		"""Toggle visibility of command list window"""
		if self.is_visible:
			self.hide()
		else:
			self.show()

	def _create_window(self):
		"""Create the tkinter window with command list"""
		# Create main window
		self.window = tk.Tk()
		self.window.title("ReaperVC Command List")

		# Calculate window size with 200px margins on all sides
		# Use reasonable default for single monitor (1920x1080 common)
		screen_width = self.window.winfo_screenwidth()
		screen_height = self.window.winfo_screenheight()

		# If total width suggests dual monitors, use half
		if screen_width > 2500:
			screen_width = screen_width // 2

		margin = 200
		window_width = screen_width - (margin * 2)
		window_height = screen_height - (margin * 2)

		# Apply max dimensions
		max_width = 1600
		max_height = 1100
		window_width = min(window_width, max_width)
		window_height = min(window_height, max_height)

		# Set geometry (width x height + x_offset + y_offset)
		self.window.geometry(f"{window_width}x{window_height}+{margin}+{margin}")

		# Set background color
		self.bg_color = "#1a1a1a"
		self.fg_color = "#ffffff"
		self.header_color = "#5594E0"
		self.pattern_color = "#aaaaaa"

		self.window.configure(bg=self.bg_color)

		# Font size control
		self.font_size = 11  # Default font size for patterns
		self.header_font_size = 14  # Default font size for headers

		# Track hidden groups
		self.hidden_groups = set()

		# Create scrollable frame
		self.main_frame = tk.Frame(self.window, bg=self.bg_color)
		self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

		# Add scrollbar
		self.canvas = tk.Canvas(self.main_frame, bg=self.bg_color, highlightthickness=0)
		self.scrollbar = tk.Scrollbar(self.main_frame, orient="vertical", command=self.canvas.yview)
		self.scrollable_frame = tk.Frame(self.canvas, bg=self.bg_color)

		self.scrollable_frame.bind(
			"<Configure>",
			lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
		)

		self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="n")
		self.canvas.configure(yscrollcommand=self.scrollbar.set)

		# Bind canvas configuration to center content
		self.canvas.bind("<Configure>", self._center_content)

		# Organize commands by group
		self.groups = self._organize_by_group()

		# Initial layout
		self._layout_groups()

		# Bind window resize to re-layout
		self.window.bind("<Configure>", self._on_resize)

		# Pack scrollbar and canvas
		self.canvas.pack(side="left", fill="both", expand=True)
		self.scrollbar.pack(side="right", fill="y")

		# Bind mouse wheel scrolling
		def _on_mousewheel(event):
			self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

		self.canvas.bind_all("<MouseWheel>", _on_mousewheel)
		self.canvas.bind_all("<Button-4>", lambda e: self.canvas.yview_scroll(-1, "units"))
		self.canvas.bind_all("<Button-5>", lambda e: self.canvas.yview_scroll(1, "units"))

		# Bottom control panel
		control_frame = tk.Frame(self.window, bg=self.bg_color)
		control_frame.pack(pady=10)

		# Font size controls
		font_label = tk.Label(
			control_frame,
			text="Font:",
			font=("Monospace", 11),
			bg=self.bg_color,
			fg=self.fg_color
		)
		font_label.pack(side=tk.LEFT, padx=(0, 10))

		font_minus = tk.Button(
			control_frame,
			text="-",
			font=("Monospace", 12, "bold"),
			command=self._decrease_font,
			bg="#333333",
			fg=self.fg_color,
			activebackground="#555555",
			width=3
		)
		font_minus.pack(side=tk.LEFT, padx=2)

		font_plus = tk.Button(
			control_frame,
			text="+",
			font=("Monospace", 12, "bold"),
			command=self._increase_font,
			bg="#333333",
			fg=self.fg_color,
			activebackground="#555555",
			width=3
		)
		font_plus.pack(side=tk.LEFT, padx=2)

		# Add close button
		close_button = tk.Button(
			control_frame,
			text="Close",
			font=("Monospace", 12),
			command=self._close_window,
			bg="#333333",
			fg=self.fg_color,
			activebackground="#555555"
		)
		close_button.pack(side=tk.LEFT, padx=(20, 0))

		# Handle window close
		self.window.protocol("WM_DELETE_WINDOW", self._close_window)

		# Track last window width for resize detection
		self.last_width = self.window.winfo_width()

		# Start the GUI event loop
		self.window.mainloop()

	def _hide_group(self, group_name):
		"""Hide a group and re-layout"""
		self.hidden_groups.add(group_name)
		self._layout_groups()

	def _increase_font(self):
		"""Increase font size"""
		self.font_size = min(20, self.font_size + 1)
		self.header_font_size = min(24, self.header_font_size + 1)
		self._layout_groups()

	def _decrease_font(self):
		"""Decrease font size"""
		self.font_size = max(6, self.font_size - 1)
		self.header_font_size = max(8, self.header_font_size - 1)
		self._layout_groups()

	def _center_content(self, event=None):
		"""Center the scrollable frame content in the canvas"""
		canvas_width = self.canvas.winfo_width()
		self.canvas.coords(self.canvas_window, canvas_width // 2, 0)

	def _on_resize(self, event):
		"""Handle window resize to adjust column count"""
		# Only respond to window resize events, not child widgets
		if event.widget != self.window:
			return

		# Get current window width
		current_width = self.window.winfo_width()

		# Only re-layout if width changed significantly (more than 100px)
		if abs(current_width - self.last_width) > 100:
			self.last_width = current_width
			self._layout_groups()

	def _layout_groups(self):
		"""Layout groups based on current window width"""
		# Clear existing widgets
		for widget in self.scrollable_frame.winfo_children():
			widget.destroy()

		# Calculate number of columns based on window width
		# Each column needs approximately 300px minimum width
		# Maximum 5 columns
		window_width = self.window.winfo_width()
		min_column_width = 300
		num_columns = max(2, min(5, window_width // min_column_width))

		# Create grid layout for groups with wrapping
		group_items = list(self.groups.items())

		current_row = 0
		current_col = 0

		for group_name, commands in group_items:
			# Skip hidden groups
			if group_name in self.hidden_groups:
				continue

			# Create frame for this group
			group_frame = tk.Frame(
				self.scrollable_frame,
				bg=self.bg_color,
				relief=tk.RAISED,
				borderwidth=1
			)
			group_frame.grid(row=current_row, column=current_col, padx=6, pady=6, sticky="new")

			# Header container (holds title and close button)
			header_container = tk.Frame(group_frame, bg=self.bg_color)
			header_container.pack(fill=tk.X, padx=8, pady=(6, 3))

			# Group header
			group_header = tk.Label(
				header_container,
				text=group_name,
				font=("Monospace", self.header_font_size, "bold"),
				bg=self.bg_color,
				fg=self.header_color,
				anchor="w"
			)
			group_header.pack(side=tk.LEFT, fill=tk.X, expand=True)

			# Hide button
			hide_button = tk.Button(
				header_container,
				text="✕",
				font=("Monospace", 10, "bold"),
				command=lambda gn=group_name: self._hide_group(gn),
				bg=self.bg_color,
				fg="#ff9900",
				activebackground="#333333",
				activeforeground="#ffffff",
				relief=tk.FLAT,
				bd=0,
				padx=4,
				pady=0,
				cursor="hand2"
			)
			hide_button.pack(side=tk.RIGHT)

			# Add separator
			separator = tk.Frame(group_frame, height=2, bg=self.header_color)
			separator.pack(fill=tk.X, padx=8)

			# Commands in this group
			for cmd_name, patterns in commands:
				# Get param_name if it exists
				cmd_config = self.commands_config['commands'].get(cmd_name, {})
				param_name = cmd_config.get('param_name', '')

				# Format patterns with param_name if it exists
				if param_name:
					patterns_text = "\n".join([f"  • {p} [{param_name}]" for p in patterns])
				else:
					patterns_text = "\n".join([f"  • {p}" for p in patterns])

				cmd_label = tk.Label(
					group_frame,
					text=patterns_text,
					font=("Monospace", self.font_size),
					bg=self.bg_color,
					fg=self.pattern_color,
					anchor="w",
					justify=tk.LEFT
				)
				cmd_label.pack(fill=tk.X, padx=10, pady=2)

			# Move to next position (wrap to next row after num_columns)
			current_col += 1
			if current_col >= num_columns:
				current_col = 0
				current_row += 1

		# Configure grid weights for equal column sizing
		for col in range(num_columns):
			self.scrollable_frame.grid_columnconfigure(col, weight=1, uniform="col")

	def _close_window(self):
		"""Close the command list window"""
		if self.window:
			self.window.destroy()
			self.window = None
			self.is_visible = False


def launch_command_list(commands_config):
	"""
	Launch command list window in a separate thread

	Args:
		commands_config: Loaded commands dictionary from YAML
	"""
	def _run():
		window = CommandListWindow(commands_config)
		window.show()

	thread = threading.Thread(target=_run, daemon=True)
	thread.start()


# Test code
if __name__ == "__main__":
	# Load test data
	commands_path = Path(__file__).parent.parent / "config" / "default_commands.yaml"
	with open(commands_path, 'r') as f:
		commands_config = yaml.safe_load(f)

	# Load custom commands
	custom_commands_path = Path(__file__).parent.parent / "config" / "custom_commands.yaml"
	if custom_commands_path.exists():
		with open(custom_commands_path, 'r') as f:
			custom_config = yaml.safe_load(f)
			if custom_config and 'commands' in custom_config:
				for cmd_name, cmd_config in custom_config['commands'].items():
					commands_config['commands'][cmd_name] = cmd_config

	# Launch window
	window = CommandListWindow(commands_config)
	window.show()
