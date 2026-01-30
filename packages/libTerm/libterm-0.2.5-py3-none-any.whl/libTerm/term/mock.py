#!/usr/bin/env python
import os
import sys
from libTerm.types import Mode, Coord, Color
from libTerm.term.cursor import Cursor
from libTerm.term.input import Stdin
# reuse TermAttrs/TermColors/TermBuffers from posix for compatibility
from libTerm.term.posix import TermAttrs, TermColors, TermBuffers


class Term():
	"""A lightweight mock Term compatible with the `posix.Term` public API.

	This class returns safe, deterministic values for attributes and methods
	used by other modules (Cursor, Size, Stdin, TermColors, TermBuffers).
	It is intended for tests and environments where a real tty is not
	available.
	"""
	MODE = Mode
	def __init__(s, *a, **k):
		s.pid = os.getpid()
		s.ppid = os.getppid() if hasattr(os, 'getppid') else s.pid
		s.fd = 0
		s.tty = None

		# Provide TermAttrs/Colors/Buffers backed by this Term so other
		# components can be instantiated without failing.
		s.attr = TermAttrs(term=s)
		s._mode = Mode.NONE

		# Minimal Size replacement: avoids ioctl and provides rows/cols/xy
		class MockSize:
			def __init__(self, term):
				self.term = term
				self.getsize = lambda: (80, 24)
				self.time = None
				self.last = None
				self.xy = Coord(79, 23)
				self._tmp = Coord(79, 23)
				self.rows = 24
				self.cols = 80
				self.history = []
				self.changed = False
				self.changing = False
			def __update__(self):
				return self.xy

		def _getsize():
			return (80, 24)
		# Cursor expects a `term` and a working `_ansi_` method; Cursor.__init__ will
		# call __update__ which calls _ansi_. Our _ansi_ returns mock coordinates.
		s.size = MockSize(term=s)
		# instantiate cursor after size so that Size is available
		s.cursor = Cursor(term=s)
		s.stdin = Stdin(term=s)
		s.color = TermColors(term=s)
		s.buffer = TermBuffers(term=s)

	def tcgetattr(s):
		# Return a termios-like list. Keep structure stable for TermAttrs.
		result = [0, 0, 0, 0, 0, 0, [0] * 32]
		return result

	def tcsetattr(s, attr, when=None):
		# noop for the mock
		result = None
		return result

	def setraw(s, when=None):
		# mimic minimal behavior used by callers: stage and update attrs
		result = None
		s.attr.stage()
		s._update_(when)
		return result

	def setcbreak(s, when=None):
		result = None
		s.attr.stage()
		s._update_(when)
		return result

	def echo(s, enable=False):
		# minimal implementation: accept call but do nothing
		result = None
		return result

	def canonical(s, enable=True):
		result = None
		return result

	@property
	def mode(s):
		result = s._mode
		return result

	@mode.setter
	def mode(s, mode):
		# follow posix.Term behavior of delegating to setmode
		result = s.setmode(mode)
		return result

	def setmode(s, mode=Mode.NONE):
		# Minimal mode handling: store and return chosen mode.
		if isinstance(mode, str):
			if mode.casefold().startswith('n'):
				mode = Mode.NORMAL
			elif mode.casefold().startswith('c'):
				mode = Mode.CONTROL
			s._mode = mode
		result = s._mode
		return result

	def _update_(s, when=None):
		# In the real Term this writes staged attrs; here we just accept the call.
		result = None
		return result

	def _ansi_(s, ansi, parser):
		# Provide deterministic mock responses for common ANSI sequences.
		# Normalize to string since callers sometimes pass Enum members.
		try:
			ansi_str = ansi if isinstance(ansi, str) else str(ansi)
		except Exception:
			ansi_str = ''
		# Cursor get position
		if ansi_str.endswith('6n') or ansi_str == '\x1b[6n':
			# if the term has a recorded last set position, return that, else origin
			try:
				result = s._last_xy
			except Exception:
				result = None
			if result is None:
				result = Coord(0, 0)
			return result
		# OSC color query sequences start with ESC ]
		if ansi_str.startswith('\x1b]'):
			# return a white foreground / black background as mock
			result = Color(255, 255, 255)
			return result
		# Fallback: try parser, but don't block — if parser raises, return Coord(0,0)
		try:
			result = parser()
		except Exception:
			result = Coord(0, 0)
		return result

