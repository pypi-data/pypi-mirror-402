# /usr/bin/env pyhthon
# !/usr/bin/env python
from select import select
import os


class Stdin():
	def __init__(s,**k):
		# super().__init__()
		s.term = s.term = k.get('term')
		s._buffer = []
		s._event = True
		s._count = 0

	@property
	def event(s):
		s._event = select([s.term.fd], [], [], 0)[0] != []
		return s._event

	@property
	def count(s):
		return s._count

	def read(s):
		s.buffer()
		ret = ''.join([i.decode('UTF-8') for i in s._buffer])
		s.flush()
		return ret

	def buffer(s):
		while select([s.term.fd], [], [], 0)[0]:
			s._buffer += [os.read(s.term.fd, 8)]
			s._count += 1
		return s._count

	def getbuffer(s):
		return s._buffer

	def getch(s):
		c=''
		if len(s._buffer) != 0:
			c = s._buffer.pop(-1)
		return c

	def flush(s):
		s._buffer = []




