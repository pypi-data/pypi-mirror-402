"""
genericlib.misc
===============
Miscellaneous utility functions for genericlib.

This module provides helper routines that support standardized program
termination and other lightweight operations. It is intended to centralize
common functionality that does not belong to a specific domain module.


Notes
-----
- Exit codes are defined in `genericlib.ECODE` and should be used consistently
  across the application.
- This module is designed for lightweight, generic helpers that simplify
  application control flow.
"""


import sys
from platform import python_version as py_version

from genericlib.constant import ECODE
from genericlib.text import decorate_list_of_line


def sys_exit(success=True, msg=''):
    """
    Terminate the program with a standardized exit code.

    This function prints an optional message and exits the program using
    predefined exit codes from `genericlib.ECODE`. It ensures consistent
    handling of success and failure termination across the application.

    Parameters
    ----------
    success : bool, optional
        Flag indicating whether the program should exit successfully.
        - True → exit with `ECODE.SUCCESS`
        - False → exit with `ECODE.BAD`
        Default is True.
    msg : str, optional
        An optional message to print before exiting. Default is an empty string.

    Returns
    -------
    None
        This function does not return. It terminates the program by calling
        `sys.exit()` with the appropriate exit code.

    Notes
    -----
    - `ECODE.SUCCESS` and `ECODE.BAD` must be defined in `genericlib.ECODE`.
    - If `msg` is provided, it is printed to standard output before termination.
    - This function is intended for controlled program termination and should
      be used instead of calling `sys.exit()` directly.
    """

    if msg:
        print(msg)
    exit_code = ECODE.SUCCESS if success else ECODE.BAD
    sys.exit(exit_code)


def ensure_tkinter_available(app_name=''):
    """
    Ensure that the `tkinter` module is available for GUI support.

    This function attempts to import `tkinter`. If successful, the module
    object is returned. If `tkinter` is unavailable or another exception
    occurs during import, the program exits gracefully with a descriptive
    framed error message.

    Parameters
    ----------
    app_name : str, optional
        The name of the application to include in error messages.
        If omitted, defaults to "The".

    Returns
    -------
    module
        The imported `tkinter` module if available.

    Raises
    ------
    SystemExit
        If `tkinter` is not installed or another import error occurs.
        A framed error message is displayed before termination.

    Notes
    -----
    - On `ModuleNotFoundError`, the error message explains that `tkinter`
      is missing and suggests installation.
    - On other exceptions, the error message includes the exception type
      and message for diagnostic purposes.
    """
    app_name = str(app_name).title() if app_name else "The"
    try:
        import tkinter as tk
        return tk
    except ModuleNotFoundError:
        items = [
            f"{app_name} application failed to start.",
            f"Python {py_version()} was detected without the tkinter module.",
            "Install tkinter to enable GUI support and retry.",
        ]
        sys_exit(success=False, msg=decorate_list_of_line(items))
    except Exception as exc:
        items = [
            f"{app_name} application could not be started due to:",
            f"*** {type(exc).__name__}: {exc}",
        ]
        sys_exit(success=False, msg=decorate_list_of_line(items))
