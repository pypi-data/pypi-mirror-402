from __future__ import annotations
from maix import _maix
import signal as signal
import sys as sys
import threading as threading
__all__: list[str] = ['register_signal_handle', 'signal', 'signal_handle', 'sys', 'threading']
def register_signal_handle():
    ...
def signal_handle(signum, frame):
    ...
