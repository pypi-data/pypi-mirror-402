# /usr/bin/env pyhthon
import io
import os
import termios
import atexit
import sys
from libTerm.types import Color, Size,Mode
from libTerm.term.cursor import  Cursor
from libTerm.term.input import  Stdin


class VirtTerm():
	MODE = Mode

	def __init__(s, *a, **k):
		s.pid = os.getpid()
		s.ppid = os.getpid()
		s.fd = sys.__stdin__.fileno()
		s.tty = 0

		s._mode = Mode.NONE
		s.mode = s.setmode
		s.attr = None
		s.cursor = Cursor(term=s)
		# s.vcursors  = {0:vCursor(s,s.cursor)}
		s.size = Size(term=s)

		s.stdin = Stdin(term=s)
		s.color = TermColors(term=s)
		s.buffer = TermBuffers(term=s)

	def tcgetattr(s):
		return termios.tcgetattr(s.fd)

	def tcsetattr(s, *a,**k):
		termios.tcsetattr(s.fd, when, attr)

	def setraw(s,  *a,**k):
		"""Put terminal into raw mode."""
		from termios import IGNBRK, BRKINT, IGNPAR, PARMRK, INPCK, ISTRIP, INLCR, IGNCR, ICRNL, IXON, IXANY, IXOFF, OPOST, PARENB, CSIZE, CS8, ECHO, ECHOE, ECHOK, ECHONL, ICANON, IEXTEN, ISIG, NOFLSH, TOSTOP
		s.attr.stage()
		# Clear all POSIX.1-2017 input mode flags.
		# See chapter 11 "General Terminal Interface"
		# of POSIX.1-2017 Base Definitions.
		s.attr.staged[IFLAG] &= ~(IGNBRK | BRKINT | IGNPAR | PARMRK | INPCK | ISTRIP | INLCR | IGNCR | ICRNL | IXON
							  | IXANY | IXOFF)
		# Do not post-process output.
		s.attr.staged[OFLAG] &= ~OPOST
		# Disable parity generation and detection; clear character size mask;
		# let character size be 8 bits.
		s.attr.staged[CFLAG] &= ~(PARENB | CSIZE)
		s.attr.staged[CFLAG] |= CS8
		# Clear all POSIX.1-2017 local mode flags.
		s.attr.staged[LFLAG] &= ~(ECHO | ECHOE | ECHOK | ECHONL | ICANON | IEXTEN | ISIG | NOFLSH | TOSTOP)
		# POSIX.1-2017, 11.1.7 Non-Canonical Mode Input Processing,
		# Case B: MIN>0, TIME=0
		# A pending read shall block until MIN (here 1) bytes are received,
		# or a signal is received.
		s.attr.staged[CC] = list(s.attr.staged[CC])
		s.attr.staged[CC][VMIN] = 1
		s.attr.staged[CC][VTIME] = 0
		s._update_(when)

	def setcbreak(s, *a,**kwargs):
		"""Put terminal into cbreak mode."""
		# this code was lifted from the tty module and adapted for being a method
		s.attr.stage()
		# Do not echo characters; disable canonical input.
		s.attr.staged[LFLAG] &= ~(ECHO | ICANON)
		# POSIX.1-2017, 11.1.7 Non-Canonical Mode Input Processing,
		# Case B: MIN>0, TIME=0
		# A pending read shall block until MIN (here 1) bytes are received,
		# or a signal is received.
		s.attr.staged[CC] = list(s.attr.staged[CC])
		s.attr.staged[CC][VMIN] = 1
		s.attr.staged[CC][VTIME] = 0
		s._update_(when)

	def echo(s,  *a,**k):
		s.attr.stage()
		s.attr.staged[3] &= ~ECHO
		if enable:
			s.attr.staged[3] |= ECHO
		s._update_()

	def canonical(s,  *a,**k):
		s.attr.stage()
		s.attr.staged[3] &= ~ICANON
		if enable:
			s.attr.staged[3] |= ICANON
		s._update_()

	def setmode(s, *a,**k):
		def Normal():
			s.cursor.show(True)
			s.echo(True)
			s.canonical(True)
			s.tcsetattr(s.attr.init)
			s._mode = Mode.NORMAL

		def Ctl():
			s.cursor.show(False)
			s.echo(False)
			s.canonical(False)
			s._mode = Mode.CONTROL
		def Input():
			s.cursor.show(True)
			s.echo(True)
			s.canonical(False)
			s._mode = Mode.INPUT


		if isinstance(mode, str):
			if mode.casefold().startswith('n'):
				mode = Mode.NORMAL
			elif mode.casefold().startswith('c'):
				mode = Mode.CONTROL

		if mode is not None and mode != Mode.NONE:
			{1: Normal, 2: Ctl}.get(mode)()
		return s._mode

	def _update_(s, *a,**k):
		s.tcsetattr(s.attr.staged, when)
		s.attr.update(s.tcgetattr())

	def _ansi_(s,  *a,**k):
		s.setcbreak()
		try:
			sys.stdout.write(ansi)
			sys.stdout.flush()
			result = parser()
		finally:
			s.tcsetattr(s.attr.restore())
		return result
#

# Expose a Term symbol so importing `Term` from this module works in tests
Term = VirtTerm
