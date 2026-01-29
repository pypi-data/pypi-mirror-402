"""
Utils for handling exceptions.
"""

import io
import traceback


def format_exception(type, value, tb) -> str:
    """Prints an exception with its traceback."""
    # Format the exception
    msg = ""
    msg += "\t%s: %s\n" % (type, str(value))

    # Format the traceback
    file_like = io.StringIO(newline="\n")
    traceback.print_tb(tb, file=file_like)
    msg += "Traceback:\n"
    msg += file_like.getvalue()

    return msg


def format_exception_from_exc(exc: Exception) -> str:
    """Helper to format from an Exception object."""
    return format_exception(type(exc), exc, exc.__traceback__)
