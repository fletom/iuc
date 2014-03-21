from datetime import datetime, timedelta
import lxml.html
import requests
import sider.types

from .. import Plugin
from utils.memoize import memoize_method


class Videotron(Plugin):
	"""For Videotron's Cable service, as well as TekSavvy, Electronic Box, and other Quebecois cable resellers."""
	
	name = 'videotron'
	
	# Videotron's endpoint is offline every night after midnight and starts returning 403 after a few requests.
	uses_redis = True
	
	def __init__(self, username, usage_cap = None):
		if usage_cap:
			self.usage_cap = float(usage_cap)
		self.username = username
	
	@property
	@memoize_method
	def data_last_retrieved(self):
		encoded_value = self.redis_get('data_last_retrieved')
		if encoded_value is None:
			return None
		return sider.types.DateTime().decode(encoded_value)
	
	@property
	@memoize_method
	def cached_raw_data(self):
		if not self.data_last_retrieved or ((datetime.now() - self.data_last_retrieved) > timedelta(minutes = 10)):
			try:
				raw_data = self.raw_data
			except self.EndpointOffline:
				self.redis_incr('was_offline')
			else:
				self.redis_incr('was_online')
				self.redis_set('data_last_retrieved', sider.types.DateTime().encode(datetime.now()))
				self.redis_set('cached_raw_data', raw_data)
				return raw_data
		
		cached_data = self.redis_get('cached_raw_data')
		
		if cached_data is None:
			raise self.EndpointOffline
		else:
			return cached_data
	
	@property
	@memoize_method
	def raw_data(self):
		
		try:
			response = requests.get(self.endpoint)
			response.raise_for_status()
		except requests.exceptions.RequestException:
			raise self.EndpointOffline
		
		if ('Total combined' not in response.text) or ('Self-service is unavailable' in response.text):
			raise self.EndpointOffline
		else:
			return response.text

		
	@property
	@memoize_method
	def etree(self):
		return lxml.html.fromstring(self.cached_raw_data)
	
	@property
	def redis_key_prefix(self):
		return '{}:{}_'.format(self.name, self.username)
	
	@property
	def endpoint(self):
		return 'https://extranet.videotron.com/services/secur/extranet/tpia/Usage.do?lang=ENGLISH&compteInternet=' + self.username
	
	@property
	def combined_usage(self):
		xpath = '/html/body/table/tr/td[2]/table/tr/td[2]/table/tr[2]/td/table/tr/td/table/tr/td/table/tr[3]/td[7]'
		return float(self.etree.xpath(xpath)[0].text)
	
	@property
	def download_usage(self):
		xpath = '/html/body/table/tr/td[2]/table/tr/td[2]/table/tr[2]/td/table/tr/td/table/tr/td/table/tr[3]/td[3]'
		return float(self.etree.xpath(xpath)[0].text)
	
	@property
	def upload_usage(self):
		xpath = '/html/body/table/tr/td[2]/table/tr/td[2]/table/tr[2]/td/table/tr/td/table/tr/td/table/tr[3]/td[5]'
		return float(self.etree.xpath(xpath)[0].text)
