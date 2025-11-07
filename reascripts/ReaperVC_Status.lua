-- ReaperVC Status
-- Check if ReaperVC is running and show status
-- Author: ReaperVC Project
-- Version: 1.0

-- Configuration
local REAPERVC_PATH = reaper.GetExtState("ReaperVC", "install_path")
if REAPERVC_PATH == "" then
	REAPERVC_PATH = os.getenv("HOME") .. "/Apps/Audio/ReaperVC"
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

function GetProcessInfo()
	local handle = io.popen("ps aux | grep 'python.*reapervc.py' | grep -v grep 2>/dev/null")
	if not handle then
		return "Unable to get process info"
	end
	local result = handle:read("*a")
	handle:close()
	return result
end

function ReadLastLog()
	local f = io.open("/tmp/reapervc.log", "r")
	if not f then
		return "No log file found"
	end

	-- Read last 10 lines
	local lines = {}
	for line in f:lines() do
		table.insert(lines, line)
		if #lines > 10 then
			table.remove(lines, 1)
		end
	end
	f:close()

	return table.concat(lines, "\n")
end

-- Main
function Main()
	local status_msg = "ReaperVC Status\n" .. string.rep("=", 50) .. "\n\n"

	if IsReaperVCRunning() then
		status_msg = status_msg .. "Status: RUNNING ✓\n\n"

		-- Show process info
		local proc_info = GetProcessInfo()
		if proc_info ~= "" then
			status_msg = status_msg .. "Process Info:\n" .. proc_info .. "\n"
		end

		-- Show recent log
		status_msg = status_msg .. "\nRecent Log:\n" .. ReadLastLog()
	else
		status_msg = status_msg .. "Status: NOT RUNNING ✗\n\n"
		status_msg = status_msg .. "Start ReaperVC with:\n"
		status_msg = status_msg .. "  Actions → ReaperVC Start\n"
		status_msg = status_msg .. "\nOr run manually:\n"
		status_msg = status_msg .. "  cd " .. REAPERVC_PATH .. "\n"
		status_msg = status_msg .. "  ./reaper-vc.sh"
	end

	-- Output to console and message box
	reaper.ShowConsoleMsg("\n" .. status_msg .. "\n\n")
	reaper.ShowMessageBox(status_msg, "ReaperVC Status", 0)
end

Main()
