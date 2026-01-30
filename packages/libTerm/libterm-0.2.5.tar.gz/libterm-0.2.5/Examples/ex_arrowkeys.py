# /usr/bin/env pyhthon

from libTerm import Term,Mode
buf = b""
term=Term()
term.mode(Mode.CONTROL)
while True:
	if term.stdin.event:
		key=term.stdin.read()
		if key == '\x1b[D':
			print("LEFT")
		elif key == '\x1b[C':
			print("RIGHT")
		elif key == '\x1b[A':
			print("UP")
		elif key == '\x1b[B':
			print("DOWN")
		print(repr(key))
