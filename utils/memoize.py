from functools import partial

class memoize_base(object):
	"""
	Memoize a method. Customized from the recipe below to allow different caches.
	
	Return values are cached on the relevant object.
	
	http://code.activestate.com/recipes/577452-a-memoize-decorator-for-instance-methods/
	"""

	@property
	def cache_name(self):
		raise NotImplementedError

	def __init__(self, func):
		self.func = func

	def __get__(self, obj, objtype = None):
		if obj is None:
			return self.func
		return partial(self, obj)

	def __call__(self, *args, **kwargs):
		obj = args[0]

		try:
			cache = getattr(obj, self.cache_name)
		except AttributeError:
			cache = {}
			setattr(obj, self.cache_name, cache)

		key = (self.func, args[1:], frozenset(kwargs.items()))
		try:
			res = cache[key]
		except KeyError:
			res = cache[key] = self.func(*args, **kwargs)
		return res

class memoize_method(memoize_base):
	"""Memoize an instance method."""
	cache_name = '_memoize_method_cache'

class memoize_class_method(memoize_base):
	"""Memoize a class method."""
	cache_name = '_memoize_class_method_cache'
