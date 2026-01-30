from datetime import datetime
import os
import sys

def timestamp(fmt="%H:%M:%S"):
    return datetime.now().strftime(fmt)

def supports_ansi():
    if os.name == "nt":
        return "ANSICON" in os.environ or "WT_SESSION" in os.environ
    return sys.stdout.isatty()
