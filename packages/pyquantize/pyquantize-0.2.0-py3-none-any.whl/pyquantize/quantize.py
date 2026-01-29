from .quantize_grid import quantize_grid
from .quantize_set import quantize_set
from collections.abc import Iterable

def quantize(*args, **kwargs):
	if len(args) > 1 and isinstance(args[1], Iterable):	# boolean short-circuiting means i dont have to nest these conditions
			return quantize_set(*args, **kwargs)
	else:
		return quantize_grid(*args, **kwargs)
