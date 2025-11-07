-- ReaperVC Telemetry Monitor
-- Displays live voice command telemetry in ReaScript console
-- Author: ReaperVC Project
-- Version: 1.0

-- Configuration
local TELEMETRY_FILE = "/tmp/reapervc_telemetry.log"
local UPDATE_INTERVAL = 0.1  -- Check for new lines every 100ms

-- State
local last_size = 0
local running = true

-- Read new lines from telemetry file
function ReadNewLines()
	-- Check if we should stop (via ExtState signal)
	local should_run = reaper.GetExtState("ReaperVC", "telemetry_running")
	if should_run == "false" then
		running = false
		-- Don't call Cleanup() here - the hide script already closed console
		return
	end

	-- Check for stop flag file (ReaperVC shutdown)
	local flag_file = io.open("/tmp/reapervc_stop_telemetry", "r")
	if flag_file then
		flag_file:close()
		os.remove("/tmp/reapervc_stop_telemetry")
		running = false
		return
	end

	local f = io.open(TELEMETRY_FILE, "r")
	if not f then
		-- File doesn't exist yet, wait
		if running then
			reaper.defer(ReadNewLines)
		end
		return
	end

	-- Get current file size
	local current_size = f:seek("end")

	if current_size > last_size then
		-- New content available
		f:seek("set", last_size)
		local new_content = f:read("*a")

		if new_content and new_content ~= "" then
			-- Display new content in console
			reaper.ShowConsoleMsg(new_content)
		end

		last_size = current_size
	end

	f:close()

	if running then
		reaper.defer(ReadNewLines)
	end
end

-- Cleanup
function Cleanup()
	running = false
	-- Don't output anything - messages reopen the console
end

-- Handle script termination
function OnExit()
	Cleanup()
end

-- Main
function Main()
	-- Clear console
	reaper.ClearConsole()

	-- Initialize
	reaper.ShowConsoleMsg("=== ReaperVC Live Telemetry ===\n\n")

	-- Check if telemetry file exists
	local f = io.open(TELEMETRY_FILE, "r")
	if f then
		-- Read header
		local header = f:read("*l")
		if header then
			reaper.ShowConsoleMsg(header .. "\n\n")
		end
		last_size = f:seek("end")
		f:close()
	else
		reaper.ShowConsoleMsg("Waiting for ReaperVC to start...\n\n")
		last_size = 0
	end

	-- Start monitoring
	ReadNewLines()
end

reaper.atexit(OnExit)
Main()
