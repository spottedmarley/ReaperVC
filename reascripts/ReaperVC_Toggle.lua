-- ReaperVC Toggle
-- Starts or stops the ReaperVC voice control system
-- Author: ReaperVC Project
-- Version: 1.0

-- Configuration
local REAPERVC_PATH = reaper.GetExtState("ReaperVC", "install_path")
if REAPERVC_PATH == "" then
	-- Path not configured - prompt user
	reaper.ShowMessageBox(
		"ReaperVC installation path not configured.\n\n" ..
		"Please run: Script: ReaperVC_SetPath.lua\n" ..
		"to set the path to your ReaperVC installation.",
		"ReaperVC Configuration Required",
		0
	)
	return
end

-- Helper Functions
function IsReaperVCRunning()
	-- Very specific check - look ONLY for Python process (not bash shells)
	local handle = io.popen("pgrep -f '^python.*src/reapervc' 2>/dev/null")
	if not handle then
		return false
	end
	local result = handle:read("*a")
	handle:close()

	-- Additional verification - check if result contains actual PID
	if result and result ~= "" then
		-- Trim whitespace and check if it's a valid number
		result = result:gsub("^%s*(.-)%s*$", "%1")
		if tonumber(result) then
			return true
		end
	end

	return false
end

function KillStaleProcesses()
	-- Kill any stale/zombie ReaperVC processes
	os.execute("pkill -9 -f 'python.*reapervc' 2>/dev/null")
end

function StartReaperVC()
	-- Check if already running
	if IsReaperVCRunning() then
		reaper.ShowMessageBox("ReaperVC is already running!", "ReaperVC", 0)
		return false
	end

	-- Verify path exists
	local f = io.open(REAPERVC_PATH .. "/reaper-vc.sh", "r")
	if not f then
		reaper.ShowMessageBox(
			"ReaperVC not found at:\n" .. REAPERVC_PATH .. "\n\n" ..
			"Please update the path in the script or set it via:\n" ..
			"Extensions → ReaperVC → Set Installation Path",
			"ReaperVC Error",
			0
		)
		return false
	end
	f:close()

	-- Start ReaperVC in background
	local cmd = string.format(
		"cd '%s' && nohup ./reaper-vc.sh > /tmp/reapervc.log 2>&1 &",
		REAPERVC_PATH
	)

	os.execute(cmd)

	-- Wait for startup (check after 3 seconds)
	local check_time = reaper.time_precise() + 3.0

	local function check_startup()
		if reaper.time_precise() < check_time then
			-- Keep waiting
			reaper.defer(check_startup)
			return
		end

		if IsReaperVCRunning() then
			-- Show simple confirmation message
			reaper.ShowMessageBox(
				"ReaperVC is listening!\n\n" ..
				"For a complete list of commands:\n"..
				"Say: \"COMMAND LIST\"\n\n"..
				"To view voice processing telemetry:\n"..
				"Say: \"CONSOLE\"",
				"ReaperVC",
				0  -- OK only
			)
		else
			reaper.ShowMessageBox(
				"Failed to start ReaperVC.\n\n" ..
				"Check the log file:\n/tmp/reapervc.log",
				"ReaperVC Error",
				0
			)
		end
	end

	check_startup()

	return true
end

function StopReaperVC()
	if not IsReaperVCRunning() then
		return false
	end

	-- Write "stop listening" command to trigger file
	-- ReaperVC will process this as a voice command and shut down gracefully with audio
	local trigger_file = "/tmp/reapervc_external_command"
	local f = io.open(trigger_file, "w")
	if f then
		f:write("stop listening")
		f:close()
	end

	-- Wait for graceful shutdown (give it 3 seconds)
	local check_time = reaper.time_precise() + 3.0

	local function verify_stopped()
		if reaper.time_precise() < check_time then
			reaper.defer(verify_stopped)
			return
		end

		if IsReaperVCRunning() then
			-- Graceful shutdown didn't work, force kill
			os.execute("pkill -9 -f 'python.*reapervc' 2>/dev/null")

			-- Final check
			reaper.defer(function()
				if IsReaperVCRunning() then
					reaper.ShowMessageBox(
						"Failed to stop ReaperVC.\n\n" ..
						"Try manually:\npkill -9 -f reapervc",
						"ReaperVC Error",
						0
					)
				end
			end)
		end
	end

	verify_stopped()

	return true
end

-- Main Logic
function Main()
	if IsReaperVCRunning() then
		-- Running - stop it
		StopReaperVC()
	else
		-- Not running - start it
		StartReaperVC()
	end
end

-- Run
Main()
