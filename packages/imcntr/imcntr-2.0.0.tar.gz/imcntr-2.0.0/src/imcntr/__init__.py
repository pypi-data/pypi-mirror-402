"""
Imaging Controller Task Interface Module.

This module provides high-level classes and helpers for interacting with an
imaging controller via a communication protocol. It defines controller tasks,
creates task submission and response-waiting objects, and exposes simple
interfaces for common operations such as moving samples, rotating, stopping
motions, and controlling the shutter.
"""

from .communication_protocol import DeviceCommunication
from .controller_api import Controller, Sample, Shutter
from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("imcntr")
except PackageNotFoundError:
    __version__ = None
