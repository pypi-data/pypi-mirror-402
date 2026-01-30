# /usr/bin/env pyhthon
from libTerm import Term,Color,Coord,Mode,Selector
import time

class Menu:
	def __init__(s,xy,*a,coord=None):
		s._tplit='{{XY}}{{COLR}}{NO}. {ITEM}\x1b[m'
		s.colr='\x1b[{SEL}38;2;192;192;192m'
		s.xy=xy
		s.selector=Selector(len(a),start=1)
		s.selected=s.selector.read
		s.items=['']
		s.menu=['']
		s.changed=[]
		s.__args__(*a)
		s.build()

	def __len__(s):
		return len(s.items)

	def __args__(s,*a):
		wit=max([len(n) for n in a])+2
		wno = len(str(len(a)))
		for i,arg in enumerate(a,start=1):
			XY = '\x1b[{Y};{X}H'.format(Y=s.xy.y + i, X=s.xy.x)
			s.items+=[s._tplit.format(NO=str(i).rjust(wno),ITEM=arg.ljust(wit))]
	def build(s):
		for i,item in enumerate(s.items,start=1):
			sel='' if i != s.selector.read() else s.sel
			s.menu+=[item.format(COLR=s.colr,SEL=sel)]


	def next(s):
		old=s.selected()
		s.changed=[s.items[s.selected-1].format(COLR=s.colr,SEL='')]
		s.selector.next()
		s.changed += [s.items[s.selector.read()-1].format(COLR=s.colr, SEL=s.sel)]
		return s.__update__()

	def prev(s):
		s.changed=[s.items[s.selector.read()-1].format(COLR=s.colr,SEL='')]
		s.selector.prev()
		s.changed += [s.items[s.selector.read()-1].format(COLR=s.colr, SEL=s.sel)]
		return s.__update__()

	def __update__(s):
		return lambda :print(''.join(s.changed),end='',flush=True)
	def __str__(s):
		return ''.join(s.menu).format(SEL='')

term=Term()
term.buffer.switch()
term.mode(Mode.CONTROL)

M=Menu(term,'aaaa','bbbbbb','cccccccccc','dd',coord=Coord(10,10))
print(M)
while True:
	if M.term.stdin.event:
		key=M.term.stdin.read()
		if key=='\x1b[B':
			update=M.next()
		elif key=='\x1b[A':
			update=M.prev()
		update()
	time.sleep(0.01)