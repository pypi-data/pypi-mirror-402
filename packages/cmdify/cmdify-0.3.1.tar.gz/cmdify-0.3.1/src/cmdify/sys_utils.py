import os
import platform
import sys
from pathlib import Path

def get_os_info():
    return platform.system() + " " + platform.release()

def get_shell_info():
    # Simple heuristic
    if platform.system() == "Windows":
        # Check if running in PowerShell
        if "PSModulePath" in os.environ:
            return "PowerShell"
        return "Command Prompt (cmd.exe)"
    else:
        return os.environ.get("SHELL", "bash")

def get_recent_history(n=3):
    system = platform.system()
    history_file = None
    
    if system == "Windows":
         appdata = os.environ.get("APPDATA")
         if appdata:
             history_file = Path(appdata) / "Microsoft/Windows/PowerShell/PSReadLine/ConsoleHost_history.txt"
    elif system in ["Linux", "Darwin"]:
         shell = os.environ.get("SHELL", "")
         if "zsh" in shell:
             history_file = Path.home() / ".zsh_history"
         else:
             history_file = Path.home() / ".bash_history"
             
    if history_file and history_file.exists():
        try:
            with open(history_file, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()
                # Return last n non-empty lines
                return [line.strip() for line in lines if line.strip()][-n:]
        except Exception:
            pass
    return []

def inject_command_to_console(command):
    """
    Injects the command into the console input buffer on Windows.
    This simulates typing the command so the user can just press Enter.
    """
    if platform.system() != "Windows":
        return

    try:
        import ctypes
        from ctypes import wintypes
    except ImportError:
        return

    kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
    
    STD_INPUT_HANDLE = -10
    hStdIn = kernel32.GetStdHandle(STD_INPUT_HANDLE)
    if hStdIn == -1 or hStdIn == 0:
        return # Not a console

    KEY_EVENT = 0x0001
    
    # Define necessary structures
    class KEY_EVENT_RECORD_Char(ctypes.Union):
        _fields_ = [("UnicodeChar", wintypes.WCHAR),
                    ("AsciiChar", ctypes.c_char)]

    class KEY_EVENT_RECORD(ctypes.Structure):
        _fields_ = [("bKeyDown", wintypes.BOOL),
                    ("wRepeatCount", wintypes.WORD),
                    ("wVirtualKeyCode", wintypes.WORD),
                    ("wVirtualScanCode", wintypes.WORD),
                    ("uChar", KEY_EVENT_RECORD_Char),
                    ("dwControlKeyState", wintypes.DWORD)]

    class INPUT_RECORD_Event(ctypes.Union):
        _fields_ = [("KeyEvent", KEY_EVENT_RECORD)]

    class INPUT_RECORD(ctypes.Structure):
        _fields_ = [("EventType", wintypes.WORD),
                    ("Event", INPUT_RECORD_Event)]

    records = []
    for char in command:
        # Key Down
        rec_down = INPUT_RECORD()
        rec_down.EventType = KEY_EVENT
        rec_down.Event.KeyEvent.bKeyDown = True
        rec_down.Event.KeyEvent.wRepeatCount = 1
        rec_down.Event.KeyEvent.wVirtualKeyCode = 0 
        rec_down.Event.KeyEvent.wVirtualScanCode = 0
        rec_down.Event.KeyEvent.uChar.UnicodeChar = char
        rec_down.Event.KeyEvent.dwControlKeyState = 0
        records.append(rec_down)

        # Key Up
        rec_up = INPUT_RECORD()
        rec_up.EventType = KEY_EVENT
        rec_up.Event.KeyEvent.bKeyDown = False
        rec_up.Event.KeyEvent.wRepeatCount = 1
        rec_up.Event.KeyEvent.wVirtualKeyCode = 0
        rec_up.Event.KeyEvent.wVirtualScanCode = 0
        rec_up.Event.KeyEvent.uChar.UnicodeChar = char
        rec_up.Event.KeyEvent.dwControlKeyState = 0
        records.append(rec_up)

    if not records:
        return

    n_records = len(records)
    lpBuffer = (INPUT_RECORD * n_records)(*records)
    lpNumberOfEventsWritten = wintypes.DWORD(0)

    success = kernel32.WriteConsoleInputW(
        hStdIn,
        lpBuffer,
        n_records,
        ctypes.byref(lpNumberOfEventsWritten)
    )
    
    if not success:
        # Silently ignore failures to inject
        pass
