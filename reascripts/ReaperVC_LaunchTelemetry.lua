-- ReaperVC Launch Telemetry (OSC-safe)
-- Wrapper to launch telemetry script via OSC
-- This script runs once and launches the telemetry monitor
-- Author: ReaperVC Project

local REAPERVC_PATH = reaper.GetExtState("ReaperVC", "install_path")
if REAPERVC_PATH == "" then
	reaper.ShowMessageBox(
		"ReaperVC installation path not configured.\n\n" ..
		"Please run: Script: ReaperVC_SetPath.lua\n" ..
		"to set the path to your ReaperVC installation.",
		"ReaperVC Configuration Required",
		0
	)
	return
end

local telemetry_path = REAPERVC_PATH .. "/reascripts/ReaperVC_Telemetry.lua"

-- First, signal any existing telemetry monitor to stop
reaper.SetExtState("ReaperVC", "telemetry_running", "false", false)

-- Write stop flag file for old instance
local flag_file = io.open("/tmp/reapervc_stop_telemetry", "w")
if flag_file then
	flag_file:write("stop")
	flag_file:close()
end

-- Wait briefly for old instance to stop
local start_time = reaper.time_precise()
while reaper.time_precise() - start_time < 0.3 do
	-- Wait
end

-- Remove stop flag
os.remove("/tmp/reapervc_stop_telemetry")

-- Now start fresh instance
reaper.SetExtState("ReaperVC", "telemetry_running", "true", false)

-- Show console first
reaper.ShowConsoleMsg("")

-- Add telemetry script and run it
local cmd_id = reaper.AddRemoveReaScript(true, 0, telemetry_path, true)

if cmd_id then
	-- Run the telemetry script
	reaper.Main_OnCommand(cmd_id, 0)
	reaper.ShowConsoleMsg("[ReaperVC] Telemetry monitor launched\n")
else
	reaper.ShowConsoleMsg("[ReaperVC] ERROR: Could not load telemetry script\n")
	reaper.ShowConsoleMsg("Path: " .. telemetry_path .. "\n")
end
