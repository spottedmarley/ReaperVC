-- ReaperVC Set Installation Path
-- Configure the installation path for ReaperVC scripts
-- Author: ReaperVC Project
-- Version: 1.0

-- Main
function Main()
	-- Get current path
	local current_path = reaper.GetExtState("ReaperVC", "install_path")
	if current_path == "" then
		current_path = os.getenv("HOME") .. "/Apps/Audio/ReaperVC"
	end

	-- Prompt for new path
	local retval, new_path = reaper.GetUserInputs(
		"ReaperVC Installation Path",
		1,
		"Installation path:",
		current_path
	)

	if not retval then
		return  -- User cancelled
	end

	-- Verify path exists
	local f = io.open(new_path .. "/reaper-vc.sh", "r")
	if not f then
		reaper.ShowMessageBox(
			"Error: reaper-vc.sh not found at:\n" .. new_path .. "\n\n" ..
			"Please enter the full path to your ReaperVC installation.",
			"Invalid Path",
			0
		)
		return
	end
	f:close()

	-- Save to ExtState (persists across REAPER sessions)
	reaper.SetExtState("ReaperVC", "install_path", new_path, true)

	reaper.ShowConsoleMsg("[ReaperVC] Installation path set to: " .. new_path .. "\n")
	reaper.ShowMessageBox(
		"ReaperVC installation path updated:\n\n" .. new_path,
		"Path Updated",
		0
	)
end

Main()
