class NoDataException(Exception):
	pass

import sys
try:
    assert sys.version[0] == '3'
except:
    raise Exception("This is a Python 3 library")

from . import core
from . import utils
