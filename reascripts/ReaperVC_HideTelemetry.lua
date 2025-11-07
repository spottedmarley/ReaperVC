-- ReaperVC Hide Telemetry
-- Signals the telemetry monitor to stop and closes the console
-- Author: ReaperVC Project

-- Close the ReaScript console window FIRST (before any messages)
reaper.Main_OnCommand(42663, 0) -- ReaScript: Show ReaScript console (toggle)

-- Signal the telemetry monitor to stop by setting ExtState
reaper.SetExtState("ReaperVC", "telemetry_running", "false", false)
