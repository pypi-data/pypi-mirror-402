#!/usr/bin/env python
import os,sys
if not sys.stdin.isatty():
	try:
		from libTerm.term.mock import Term
	except Exception:
		from libTerm.term.virt import Term

elif os.name == 'nt':
	from libTerm.term.winnt import Term
else:
	from libTerm.term.posix import Term

