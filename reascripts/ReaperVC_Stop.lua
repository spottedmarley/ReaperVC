-- ReaperVC Stop
-- Stops the ReaperVC voice control system
-- Author: ReaperVC Project
-- Version: 1.0

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

function KillAllProcesses()
	-- Kill all ReaperVC processes (including stale ones)
	os.execute("pkill -9 -f 'python.*reapervc' 2>/dev/null")
end

-- Main
function Main()
	-- Signal telemetry script to stop
	reaper.SetExtState("ReaperVC", "telemetry_stop", "1", false)

	-- Kill all processes (SIGKILL to ensure they stop)
	KillAllProcesses()

	-- Clean up log files
	os.execute("rm -f /tmp/reapervc.log 2>/dev/null")
	os.execute("rm -f /tmp/reapervc_telemetry.log 2>/dev/null")

	-- Wait a moment and verify
	reaper.defer(function()
		if IsReaperVCRunning() then
			reaper.ShowMessageBox(
				"Warning: Some processes may still be running.\n\n" ..
				"Try manually:\npkill -9 -f reapervc",
				"ReaperVC",
				0
			)
		end
	end)
end

Main()
