from collections import namedtuple
import calendar
from datetime import date, timedelta
from os import environ as env
import redis

billing_period = namedtuple('billing_period', 'start end')

class Plugin(object):
	
	name = None
	usage_cap = None
	# Use this when your ISP's usage checking endpoint is unstable or strictly rate-limited.
	use_cache = False
	redis = redis.Redis.from_url(env.get('REDIS_URL') or env.get('REDISCLOUD_URL') or 'redis://localhost:6379')
	
	class EndpointOffline(Exception):
		pass
	
	@property
	def download_usage(self):
		raise NotImplementedError
	
	@property
	def upload_usage(self):
		raise NotImplementedError
	
	@property
	def combined_usage(self):
		raise NotImplementedError
	
	@property
	def usage_percentage(self):
		if self.usage_cap:
			return '({0:.2%})'.format(self.combined_usage / self.usage_cap)
		else:
			return None
	
	@property
	def redis_key_prefix(self):
		raise NotImplementedError
	
	def __getattr__(self, name):
		if name.startswith('redis_'):
			def redis_method(key, *args, **kwargs):
				return getattr(self.redis, name[len('redis_'):])(self.redis_key_prefix + key, *args, **kwargs)
			return redis_method
		
		raise AttributeError("'{0}' object has no attribute '{1}'".format(self.__class__.__name__, name))
	
	@property
	def data_last_retrieved(self):
		return None
	
	@property
	def billing_period(self):
		today = date.today()
		return billing_period(
			today.replace(day = 1),
			today.replace(day = calendar.monthrange(today.year, today.month)[1]),
		) 

from .videotron import Videotron

__all__ = [
	'Plugin',
	'Videotron',
]
