"""
Module for managing Windows related tasks
"""
import time
import psutil
import pygetwindow as gw


def kill_process_by_name(process_name):
    """
    Lukker job fra joblisten med det givne navn (f.eks. 'BogV.exe', 'KMDLOGON.EXE' etc.)
    """
    for process in psutil.process_iter(['pid', 'name']):
        if process.info['name'] == process_name:
            # Get the process ID (PID) for the matching process
            pid = process.info['pid']
            try:
                # Create a Process object for the specified PID
                process = psutil.Process(pid)
                process.terminate()
                print(f"Process {process_name} with PID {pid} terminated.")
            except psutil.NoSuchProcess as e:
                print(f"Error: {e}")
            break


def close_window_by_title(window_title, target_edge_windows=False):
    """Closes any open window(s) with a title that contains the specified string.
    Ignores Edge windows if target_edge_windows is set to False."""
    time.sleep(3)  # Pause to ensure any recently opened windows are fully loaded
    matching_windows = [window for window in gw.getAllTitles() if window_title in window]

    if matching_windows:
        for title in matching_windows:
            # Check if the window is an Edge window and if it should be ignored
            if "Microsoft\u200b Edge" in title and target_edge_windows is False:
                print(f"Skipping Edge window with title '{title}'.")
                continue  # Skip closing this Edge window

            # Close each window with a matching title
            gw.getWindowsWithTitle(title)[0].close()
            print(f"Window with title '{title}' closed successfully.")
    else:
        print("No open windows with the specified title found.")
