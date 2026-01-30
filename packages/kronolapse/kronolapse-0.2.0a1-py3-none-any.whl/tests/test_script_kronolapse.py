# -*- mode: python -*-
# -*- coding: utf-8 -*-
#
# test_script_kronolapse.py
#
# This test check the functionality for script krononolapse.

import sys
import platform
import subprocess


# Check success or failure for the command
def parse_command(command: list) -> bool:
    try:
        subprocess.run(command,
                       capture_output=True,
                       text=True,
                       check=True)
        print("Command '{}' executed successfully!".format(command[0]))
        status = True
        return status
    except subprocess.CalledProcessError as e:
        print("Failed input:\n{}".format(e), file=sys.stderr)
        print("Error output:\n{}".format(e.stderr), file=sys.stderr)
        status = False
        return status
    except FileNotFoundError:
        print("Failed installation: command '{}' not found.".format(command[0]))
        status = False
        return status


# Define command according to OS
def command_platform() -> str:
    # For Windows
    if platform.system() == "Windows":
        str_exe = r".\venv\Scripts\python.exe"
    # For Linux/macOS
    else:
        str_exe = "./venv/bin/python"
    return str_exe


# Check read of schedule file
def test_script_read_schedule() -> None:
    cmd = [command_platform(), "-m", "kronolapse", "-s", "schedule_test.csv"]
    process = parse_command(cmd)
    assert process is True, "The schedule was not displayed correctly"


# Check the schedule is shown
def test_script_show_schedule() -> None:
    cmd = [command_platform(), "-m", "kronolapse", "schedule_test.csv"]
    process = parse_command(cmd)
    assert process is True, "The schedule was not displayed correctly"
