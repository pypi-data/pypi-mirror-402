# /usr/bin/env pyhthon
from libTerm import Term
from libTerm import Coord,Mode
import time



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
	def down(s):
		print('\x1b[B\x1b[D', end='', flush=True)
		s.addpiece()
	def up(s):
		print('\x1b[A\x1b[D', end='', flush=True)
		s.addpiece()
	def right(s):
		print('', end='', flush=True)
		s.addpiece()
	def left(s):
		print('\x1b[D\x1b[D', end='', flush=True)
		s.addpiece()

t=Term()
t.echo(False)
t.cursor.show(False)
print('\n\n\n\n\n\n\n')
t.mode=Mode.CONTROL
vert=t.size.xy.y
print(vert)
snake=Snake(t,speed=100)
time.sleep(2)
snake.piece = '░'
for i in range(8):
	for i in range(vert):
		snake.down()
		time.sleep(snake.speed)
	for i in range(6):
		snake.right()
		time.sleep(snake.speed)
	for i in range(vert):
		snake.up()
		time.sleep(snake.speed)
	for i in range(6):
		snake.right()
		time.sleep(snake.speed)

while t.cursor.store.selected:
	snake.rempiece()
	time.sleep(snake.speed)


