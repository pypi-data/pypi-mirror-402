# /usr/bin/env pyhthon

import time
from libTerm import Term
from libTerm import Coord,Mode,Color

class Snake():
	def __init__(s,t,speed=10):
		s.speed=1 / (speed or 1)
		s.term=t
		s.piece=''

	def addpiece(s):
		print(s.piece, end='', flush=True)
		s.term.cursor.save()

	def rempiece(s):
		s.term.cursor.undo()
		print('\x1b[D ', end='', flush=True)

term=Term()
term.mode=Mode.CONTROL
snake=Snake(term)
term.buffer.switch()
print('\x1b[J\x1b[1;1HPress one of up,down,left,right to start and  q to quit!')
while True:
	if term.stdin.event:
		key=term.stdin.read()
		if key=='\x1b[A':
			snake.piece='\x1b[A\x1b[D░'
		elif key=="\x1b[B":
			snake.piece='\x1b[B\x1b[D░'
		elif key=='\x1b[C':
			snake.piece='░'
		elif key=='\x1b[D':
			snake.piece = '\x1b[D\x1b[D░'
		elif key=='q':
			while term.cursor.store.selected:
				snake.rempiece()
				time.sleep(snake.speed)
			break
	if snake.piece!='':
		snake.addpiece()
	time.sleep(snake.speed)
term.buffer.default()
