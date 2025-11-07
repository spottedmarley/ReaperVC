-- ReaperVC Cleanup and Start
-- Kills any stale processes and starts ReaperVC fresh
-- Author: ReaperVC Project
-- Version: 1.0
-- Use this if Toggle/Start scripts are having issues

-- Configuration
local REAPERVC_PATH = reaper.GetExtState("ReaperVC", "install_path")
if REAPERVC_PATH == "" then
	-- Default path - update this to match your installation
	REAPERVC_PATH = os.getenv("HOME") .. "/Apps/Audio/ReaperVC"
end

-- Main
function Main()
	reaper.ShowConsoleMsg("[ReaperVC Cleanup] Starting cleanup...\n")

	-- Kill ALL ReaperVC processes
	reaper.ShowConsoleMsg("[ReaperVC Cleanup] Killing all ReaperVC processes...\n")
	os.execute("pkill -9 -f 'python.*reapervc' 2>/dev/null")

	-- Clean up log file
	reaper.ShowConsoleMsg("[ReaperVC Cleanup] Removing old log file...\n")
	os.execute("rm -f /tmp/reapervc.log 2>/dev/null")

	-- Verify path exists
	local f = io.open(REAPERVC_PATH .. "/reaper-vc.sh", "r")
	if not f then
		reaper.ShowMessageBox(
			"ReaperVC not found at:\n" .. REAPERVC_PATH .. "\n\n" ..
			"Please run ReaperVC_SetPath.lua to configure.",
			"ReaperVC Error",
			0
		)
		return
	end
	f:close()

	-- Start fresh
	reaper.ShowConsoleMsg("[ReaperVC Cleanup] Starting ReaperVC...\n")
	local cmd = string.format(
		"cd '%s' && nohup ./reaper-vc.sh > /tmp/reapervc.log 2>&1 &",
		REAPERVC_PATH
	)
	os.execute(cmd)

	-- Show success message (don't check immediately, let it start)
	reaper.ShowConsoleMsg("[ReaperVC Cleanup] Started! Initializing...\n")
	reaper.ShowConsoleMsg("[ReaperVC Cleanup] Check Status script in a few seconds to verify.\n")
	reaper.ShowMessageBox(
		"ReaperVC cleanup complete!\n\n" ..
		"Starting fresh...\n" ..
		"Wait for welcome sound, then ready for voice commands!\n\n" ..
		"Run ReaperVC_Status to check if ready.",
		"Success",
		0
	)
end

Main()
