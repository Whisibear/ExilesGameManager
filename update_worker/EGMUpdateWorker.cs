using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Globalization;
using System.IO;
using System.Text;
using System.Threading;

[assembly: System.Reflection.AssemblyTitle("Exiles Game Manager Update Worker")]
[assembly: System.Reflection.AssemblyDescription("Native update handoff worker for Exiles Game Manager")]
[assembly: System.Reflection.AssemblyCompany("Whisibear EGM")]
[assembly: System.Reflection.AssemblyProduct("Exiles Game Manager")]
[assembly: System.Reflection.AssemblyCopyright("Copyright © 2026 Whisibear EGM")]
[assembly: System.Reflection.AssemblyVersion("0.8.1.5")]
[assembly: System.Reflection.AssemblyFileVersion("0.8.1.5")]

internal static class Program
{
    private const int ParentWaitSeconds = 15;

    private static int Main(string[] args)
    {
        Dictionary<string, string> options;
        try
        {
            options = ParseArguments(args);
        }
        catch (Exception ex)
        {
            return FailWithoutLog("Invalid UpdateWorker arguments: " + ex.Message);
        }

        string installer = Required(options, "installer");
        string restartExe = Required(options, "restart");
        string marker = Required(options, "marker");
        string handoffLog = Required(options, "handoff-log");
        string installerLog = Required(options, "installer-log");
        string fromVersion = Get(options, "from", "unknown");
        string toVersion = Get(options, "to", "unknown");
        string sha256 = Get(options, "sha256", string.Empty);
        int parentPid = ParseInt(Get(options, "parent-pid", "0"));

        long startedAt = DateTimeOffset.UtcNow.ToUnixTimeSeconds();
        int installerExitCode = -1;
        bool installerStarted = false;
        bool restartStarted = false;
        string error = null;

        try
        {
            EnsureParentDirectory(handoffLog);
            Log(handoffLog, "UpdateWorker started.");
            Log(handoffLog, "Installer: " + installer);
            Log(handoffLog, "Restart executable: " + restartExe);
            Log(handoffLog, "Parent PID: " + parentPid.ToString(CultureInfo.InvariantCulture));

            if (!File.Exists(installer))
            {
                throw new FileNotFoundException("Downloaded installer was not found.", installer);
            }

            WaitForParent(parentPid, handoffLog);

            string arguments = "/UPDATE /VERYSILENT /SUPPRESSMSGBOXES /NORESTART /NORESTARTEGM /SP- /LOG=\"" + installerLog + "\"";
            Log(handoffLog, "Starting installer with silent update arguments.");

            ProcessStartInfo setupInfo = new ProcessStartInfo
            {
                FileName = installer,
                Arguments = arguments,
                WorkingDirectory = Path.GetDirectoryName(installer) ?? Environment.CurrentDirectory,
                UseShellExecute = false,
                CreateNoWindow = true,
                WindowStyle = ProcessWindowStyle.Hidden
            };

            using (Process setup = Process.Start(setupInfo))
            {
                if (setup == null)
                {
                    throw new InvalidOperationException("Windows did not create the installer process.");
                }
                installerStarted = true;
                Log(handoffLog, "Installer started with PID " + setup.Id.ToString(CultureInfo.InvariantCulture) + ".");
                setup.WaitForExit();
                installerExitCode = setup.ExitCode;
            }

            Log(handoffLog, "Installer exited with code " + installerExitCode.ToString(CultureInfo.InvariantCulture) + ".");
            if (installerExitCode != 0)
            {
                throw new InvalidOperationException("Installer returned exit code " + installerExitCode.ToString(CultureInfo.InvariantCulture) + ".");
            }

            if (!File.Exists(restartExe))
            {
                throw new FileNotFoundException("Updated EGM executable was not found.", restartExe);
            }

            ProcessStartInfo restartInfo = new ProcessStartInfo
            {
                FileName = restartExe,
                WorkingDirectory = Path.GetDirectoryName(restartExe) ?? Environment.CurrentDirectory,
                UseShellExecute = true
            };
            Process restarted = Process.Start(restartInfo);
            if (restarted == null)
            {
                throw new InvalidOperationException("Windows did not restart EGM.");
            }
            restartStarted = true;
            Log(handoffLog, "Updated EGM started with PID " + restarted.Id.ToString(CultureInfo.InvariantCulture) + ".");
            WriteMarker(marker, true, fromVersion, toVersion, installer, installerLog, handoffLog, sha256, startedAt, installerStarted, restartStarted, installerExitCode, null);
            return 0;
        }
        catch (Exception ex)
        {
            error = ex.ToString();
            TryLog(handoffLog, "Automatic update failed: " + error);
            WriteMarker(marker, false, fromVersion, toVersion, installer, installerLog, handoffLog, sha256, startedAt, installerStarted, restartStarted, installerExitCode, error);

            if (!restartStarted && File.Exists(restartExe))
            {
                try
                {
                    ProcessStartInfo fallbackInfo = new ProcessStartInfo
                    {
                        FileName = restartExe,
                        WorkingDirectory = Path.GetDirectoryName(restartExe) ?? Environment.CurrentDirectory,
                        UseShellExecute = true
                    };
                    Process fallback = Process.Start(fallbackInfo);
                    if (fallback != null)
                    {
                        TryLog(handoffLog, "Existing EGM installation restarted after update failure.");
                    }
                }
                catch (Exception restartError)
                {
                    TryLog(handoffLog, "Fallback restart failed: " + restartError);
                }
            }
            return 1;
        }
    }

    private static void WaitForParent(int parentPid, string logPath)
    {
        if (parentPid <= 0)
        {
            return;
        }
        Stopwatch timer = Stopwatch.StartNew();
        while (timer.Elapsed < TimeSpan.FromSeconds(ParentWaitSeconds))
        {
            try
            {
                using (Process parent = Process.GetProcessById(parentPid))
                {
                    if (parent.HasExited)
                    {
                        Log(logPath, "EGM parent process exited.");
                        return;
                    }
                }
            }
            catch (ArgumentException)
            {
                Log(logPath, "EGM parent process exited.");
                return;
            }
            Thread.Sleep(250);
        }
        Log(logPath, "Parent process still exists after bounded wait; Setup will close EGM through the installer shutdown logic.");
    }

    private static Dictionary<string, string> ParseArguments(string[] args)
    {
        Dictionary<string, string> result = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
        for (int index = 0; index < args.Length; index++)
        {
            string current = args[index];
            if (!current.StartsWith("--", StringComparison.Ordinal))
            {
                continue;
            }
            string key = current.Substring(2);
            if (index + 1 >= args.Length)
            {
                throw new ArgumentException("Missing value for --" + key);
            }
            result[key] = args[++index];
        }
        return result;
    }

    private static string Required(Dictionary<string, string> options, string key)
    {
        string value;
        if (!options.TryGetValue(key, out value) || string.IsNullOrWhiteSpace(value))
        {
            throw new ArgumentException("Required argument --" + key + " is missing.");
        }
        return value;
    }

    private static string Get(Dictionary<string, string> options, string key, string fallback)
    {
        string value;
        return options.TryGetValue(key, out value) ? value : fallback;
    }

    private static int ParseInt(string value)
    {
        int result;
        return int.TryParse(value, NumberStyles.Integer, CultureInfo.InvariantCulture, out result) ? result : 0;
    }

    private static void Log(string path, string message)
    {
        EnsureParentDirectory(path);
        File.AppendAllText(path, "[" + DateTimeOffset.UtcNow.ToString("o", CultureInfo.InvariantCulture) + "] " + message + Environment.NewLine, new UTF8Encoding(false));
    }

    private static void TryLog(string path, string message)
    {
        try { Log(path, message); } catch { }
    }

    private static void EnsureParentDirectory(string path)
    {
        string directory = Path.GetDirectoryName(path);
        if (!string.IsNullOrEmpty(directory))
        {
            Directory.CreateDirectory(directory);
        }
    }

    private static void WriteMarker(string path, bool success, string fromVersion, string toVersion, string installer, string installerLog, string handoffLog, string sha256, long startedAt, bool installerStarted, bool restartStarted, int exitCode, string error)
    {
        try
        {
            EnsureParentDirectory(path);
            string json = "{" +
                "\"version\":\"" + Escape(toVersion) + "\"," +
                "\"fromVersion\":\"" + Escape(fromVersion) + "\"," +
                "\"installer\":\"" + Escape(Path.GetFileName(installer)) + "\"," +
                "\"installerPath\":\"" + Escape(installer) + "\"," +
                "\"installerLog\":\"" + Escape(installerLog) + "\"," +
                "\"handoffLog\":\"" + Escape(handoffLog) + "\"," +
                "\"sha256\":\"" + Escape(sha256) + "\"," +
                "\"sha256Verified\":true," +
                "\"startedAt\":" + startedAt.ToString(CultureInfo.InvariantCulture) + "," +
                "\"success\":" + (success ? "true" : "false") + "," +
                "\"installerStarted\":" + (installerStarted ? "true" : "false") + "," +
                "\"restartStarted\":" + (restartStarted ? "true" : "false") + "," +
                "\"exitCode\":" + exitCode.ToString(CultureInfo.InvariantCulture) + "," +
                "\"error\":" + (error == null ? "null" : "\"" + Escape(error) + "\"") + "," +
                "\"completedAt\":" + DateTimeOffset.UtcNow.ToUnixTimeSeconds().ToString(CultureInfo.InvariantCulture) +
                "}";
            File.WriteAllText(path, json, new UTF8Encoding(false));
        }
        catch { }
    }

    private static string Escape(string value)
    {
        if (value == null) return string.Empty;
        return value.Replace("\\", "\\\\").Replace("\"", "\\\"").Replace("\r", "\\r").Replace("\n", "\\n");
    }

    private static int FailWithoutLog(string message)
    {
        try { Console.Error.WriteLine(message); } catch { }
        return 2;
    }
}
