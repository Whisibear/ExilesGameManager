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
    private const string JobEnvironmentVariable = "EGM_UPDATE_JOB";

    private static int Main()
    {
        string fallbackLog = Path.Combine(
            AppDomain.CurrentDomain.BaseDirectory,
            "update_worker_fallback.log"
        );

        Dictionary<string, string> options;
        string jobPath = Environment.GetEnvironmentVariable(JobEnvironmentVariable);

        try
        {
            if (string.IsNullOrWhiteSpace(jobPath))
            {
                throw new InvalidOperationException(
                    JobEnvironmentVariable + " is missing."
                );
            }

            jobPath = ValidatePath(jobPath, true, "job");
            options = ReadJob(jobPath);
        }
        catch (Exception ex)
        {
            TryLog(fallbackLog, "Unable to read update job: " + ex);
            return 2;
        }

        string installer;
        string restartExe;
        string marker;
        string handoffLog;
        string installerLog;
        string fromVersion;
        string toVersion;
        string sha256;
        int parentPid;

        try
        {
            installer = ValidatePath(Required(options, "installer"), true, "installer");
            restartExe = ValidatePath(Required(options, "restart"), false, "restart executable");
            marker = ValidatePath(Required(options, "marker"), false, "completion marker");
            handoffLog = ValidatePath(Required(options, "handoff-log"), false, "worker log");
            installerLog = ValidatePath(Required(options, "installer-log"), false, "installer log");
            fromVersion = Get(options, "from", "unknown");
            toVersion = Get(options, "to", "unknown");
            sha256 = Get(options, "sha256", string.Empty);
            parentPid = ParseInt(Get(options, "parent-pid", "0"));
        }
        catch (Exception ex)
        {
            TryLog(fallbackLog, "Invalid update job values: " + ex);
            return 3;
        }

        long startedAt = DateTimeOffset.UtcNow.ToUnixTimeSeconds();
        int installerExitCode = -1;
        bool installerStarted = false;
        bool restartStarted = false;
        string error = null;

        try
        {
            EnsureParentDirectory(handoffLog);
            Log(handoffLog, "UpdateWorker started.");
            Log(handoffLog, "Job: " + jobPath);
            Log(handoffLog, "Installer: " + installer);
            Log(handoffLog, "Restart executable: " + restartExe);
            Log(handoffLog, "Parent PID: " + parentPid.ToString(CultureInfo.InvariantCulture));

            WaitForParent(parentPid, handoffLog);

            string setupArguments =
                "/UPDATE /VERYSILENT /SUPPRESSMSGBOXES /NORESTART " +
                "/NORESTARTEGM /SP- /LOG=\"" + installerLog + "\"";

            ProcessStartInfo setupInfo = new ProcessStartInfo();
            setupInfo.FileName = installer;
            setupInfo.Arguments = setupArguments;
            setupInfo.WorkingDirectory =
                Path.GetDirectoryName(installer) ?? Environment.CurrentDirectory;
            setupInfo.UseShellExecute = false;
            setupInfo.CreateNoWindow = true;
            setupInfo.WindowStyle = ProcessWindowStyle.Hidden;

            Log(handoffLog, "Starting installer without shell execution.");
            using (Process setup = Process.Start(setupInfo))
            {
                if (setup == null)
                {
                    throw new InvalidOperationException(
                        "Windows did not create the installer process."
                    );
                }

                installerStarted = true;
                Log(
                    handoffLog,
                    "Installer started with PID " +
                    setup.Id.ToString(CultureInfo.InvariantCulture) +
                    "."
                );
                setup.WaitForExit();
                installerExitCode = setup.ExitCode;
            }

            Log(
                handoffLog,
                "Installer exited with code " +
                installerExitCode.ToString(CultureInfo.InvariantCulture) +
                "."
            );

            if (installerExitCode != 0)
            {
                throw new InvalidOperationException(
                    "Installer returned exit code " +
                    installerExitCode.ToString(CultureInfo.InvariantCulture) +
                    "."
                );
            }

            restartExe = ValidatePath(
                restartExe,
                true,
                "updated EGM executable"
            );

            ProcessStartInfo restartInfo = new ProcessStartInfo();
            restartInfo.FileName = restartExe;
            restartInfo.WorkingDirectory =
                Path.GetDirectoryName(restartExe) ?? Environment.CurrentDirectory;
            restartInfo.UseShellExecute = false;
            restartInfo.CreateNoWindow = false;

            Log(handoffLog, "Starting updated EGM without shell execution.");
            Process restarted = Process.Start(restartInfo);
            if (restarted == null)
            {
                throw new InvalidOperationException(
                    "Windows did not restart EGM."
                );
            }

            restartStarted = true;
            Log(
                handoffLog,
                "Updated EGM started with PID " +
                restarted.Id.ToString(CultureInfo.InvariantCulture) +
                "."
            );

            WriteMarker(
                marker,
                true,
                fromVersion,
                toVersion,
                installer,
                installerLog,
                handoffLog,
                sha256,
                startedAt,
                installerStarted,
                restartStarted,
                installerExitCode,
                null
            );

            TryDelete(jobPath, handoffLog);
            return 0;
        }
        catch (Exception ex)
        {
            error = ex.ToString();
            TryLog(handoffLog, "Automatic update failed: " + error);

            WriteMarker(
                marker,
                false,
                fromVersion,
                toVersion,
                installer,
                installerLog,
                handoffLog,
                sha256,
                startedAt,
                installerStarted,
                restartStarted,
                installerExitCode,
                error
            );

            if (!restartStarted && File.Exists(restartExe))
            {
                try
                {
                    ProcessStartInfo fallbackInfo = new ProcessStartInfo();
                    fallbackInfo.FileName = restartExe;
                    fallbackInfo.WorkingDirectory =
                        Path.GetDirectoryName(restartExe) ??
                        Environment.CurrentDirectory;
                    fallbackInfo.UseShellExecute = false;
                    fallbackInfo.CreateNoWindow = false;

                    Process fallback = Process.Start(fallbackInfo);
                    if (fallback != null)
                    {
                        TryLog(
                            handoffLog,
                            "Existing EGM installation restarted after update failure."
                        );
                    }
                }
                catch (Exception restartError)
                {
                    TryLog(
                        handoffLog,
                        "Fallback restart failed: " + restartError
                    );
                }
            }

            return 1;
        }
    }

    private static Dictionary<string, string> ReadJob(string path)
    {
        Dictionary<string, string> result =
            new Dictionary<string, string>(
                StringComparer.OrdinalIgnoreCase
            );

        foreach (string rawLine in File.ReadAllLines(path, Encoding.ASCII))
        {
            if (string.IsNullOrWhiteSpace(rawLine))
            {
                continue;
            }

            int separator = rawLine.IndexOf('=');
            if (separator <= 0)
            {
                throw new InvalidDataException("Invalid update job line.");
            }

            string key = rawLine.Substring(0, separator);
            string encodedValue = rawLine.Substring(separator + 1);
            byte[] bytes = Convert.FromBase64String(encodedValue);
            result[key] = Encoding.UTF8.GetString(bytes);
        }

        return result;
    }

    private static string ValidatePath(
        string value,
        bool mustExist,
        string description
    )
    {
        string raw = value == null ? string.Empty : value.Trim();
        if (raw.Length == 0 ||
            raw == "\\" ||
            raw == "\\\\" ||
            raw == "/" ||
            raw == ".")
        {
            throw new InvalidDataException(
                "Unsafe " + description + " path: " + raw
            );
        }

        string fullPath = Path.GetFullPath(raw);
        string trimmed = fullPath.Trim();

        if (!Path.IsPathRooted(fullPath) ||
            trimmed == "\\" ||
            trimmed == "\\\\" ||
            trimmed == "/" ||
            trimmed == ".")
        {
            throw new InvalidDataException(
                "Unsafe " + description + " path: " + raw
            );
        }

        if (mustExist && !File.Exists(fullPath))
        {
            throw new FileNotFoundException(
                "Required " + description + " file was not found.",
                fullPath
            );
        }

        return fullPath;
    }

    private static void WaitForParent(int parentPid, string logPath)
    {
        if (parentPid <= 0)
        {
            Log(logPath, "No parent PID supplied; continuing.");
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

        Log(
            logPath,
            "Parent process still exists after bounded wait; " +
            "Setup will use the installer shutdown logic."
        );
    }

    private static string Required(
        Dictionary<string, string> options,
        string key
    )
    {
        string value;
        if (!options.TryGetValue(key, out value) ||
            string.IsNullOrWhiteSpace(value))
        {
            throw new ArgumentException(
                "Required job value " + key + " is missing."
            );
        }

        return value;
    }

    private static string Get(
        Dictionary<string, string> options,
        string key,
        string fallback
    )
    {
        string value;
        return options.TryGetValue(key, out value) ? value : fallback;
    }

    private static int ParseInt(string value)
    {
        int result;
        return int.TryParse(
            value,
            NumberStyles.Integer,
            CultureInfo.InvariantCulture,
            out result
        ) ? result : 0;
    }

    private static void Log(string path, string message)
    {
        EnsureParentDirectory(path);
        File.AppendAllText(
            path,
            "[" +
            DateTimeOffset.UtcNow.ToString(
                "o",
                CultureInfo.InvariantCulture
            ) +
            "] " +
            message +
            Environment.NewLine,
            new UTF8Encoding(false)
        );
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

    private static void TryDelete(string path, string logPath)
    {
        try
        {
            if (File.Exists(path))
            {
                File.Delete(path);
            }
        }
        catch (Exception ex)
        {
            TryLog(logPath, "Unable to delete update job: " + ex.Message);
        }
    }

    private static void WriteMarker(
        string path,
        bool success,
        string fromVersion,
        string toVersion,
        string installer,
        string installerLog,
        string handoffLog,
        string sha256,
        long startedAt,
        bool installerStarted,
        bool restartStarted,
        int exitCode,
        string error
    )
    {
        try
        {
            EnsureParentDirectory(path);
            string json =
                "{" +
                "\"version\":\"" + Escape(toVersion) + "\"," +
                "\"fromVersion\":\"" + Escape(fromVersion) + "\"," +
                "\"installer\":\"" +
                Escape(Path.GetFileName(installer)) +
                "\"," +
                "\"installerPath\":\"" + Escape(installer) + "\"," +
                "\"installerLog\":\"" + Escape(installerLog) + "\"," +
                "\"handoffLog\":\"" + Escape(handoffLog) + "\"," +
                "\"sha256\":\"" + Escape(sha256) + "\"," +
                "\"sha256Verified\":true," +
                "\"startedAt\":" +
                startedAt.ToString(CultureInfo.InvariantCulture) +
                "," +
                "\"success\":" + (success ? "true" : "false") + "," +
                "\"installerStarted\":" +
                (installerStarted ? "true" : "false") +
                "," +
                "\"restartStarted\":" +
                (restartStarted ? "true" : "false") +
                "," +
                "\"exitCode\":" +
                exitCode.ToString(CultureInfo.InvariantCulture) +
                "," +
                "\"error\":" +
                (
                    error == null
                    ? "null"
                    : "\"" + Escape(error) + "\""
                ) +
                "," +
                "\"completedAt\":" +
                DateTimeOffset.UtcNow
                    .ToUnixTimeSeconds()
                    .ToString(CultureInfo.InvariantCulture) +
                "}";

            File.WriteAllText(
                path,
                json,
                new UTF8Encoding(false)
            );
        }
        catch { }
    }

    private static string Escape(string value)
    {
        if (value == null)
        {
            return string.Empty;
        }

        return value
            .Replace("\\", "\\\\")
            .Replace("\"", "\\\"")
            .Replace("\r", "\\r")
            .Replace("\n", "\\n");
    }
}
