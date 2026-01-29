"""Executor subprocess for running experiment tasks and evaluations.

This module implements the subprocess side of the executor protocol.
The Go CLI spawns this as a subprocess and communicates via JSON-lines over stdin/stdout.
"""

from __future__ import annotations
