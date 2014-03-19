import argh
from argh.decorators import arg
from os import environ as env
import tinysmtp

from plugins import *


plugins = {p.name: p for p in Plugin.__subclasses__()}
default_conf_string = env.get('IUC_CONF')

def get_plugin_by_conf_string(conf_string):
	plugin_name, _, plugin_args = conf_string.partition(':')
	
	return plugins[plugin_name](*plugin_args.split(','))

default_plugin = get_plugin_by_conf_string(default_conf_string)

def run():
	from app import app
	app.run(debug = True)

@arg('max_usage', type = int)
def check(max_usage, warn_email = None, from_email = None):
	plugin = default_plugin
	
	try:
		usage = plugin.combined_usage
	except plugin.EndpointOffline:
		print "Endpoint Offline :/"
		return
	
	if usage > max_usage:
		print "Threshold exceeded: {} GB exceeds {} GB by {} GB.".format(usage, max_usage, usage - max_usage)
		if warn_email:
			# A key that represents this particular warning for this particular billing period
			warn_email_sent_key = '{}{}{} was sent'.format(plugin.billing_period, max_usage, warn_email)
			
			if plugin.redis_get(warn_email_sent_key):
				return
			
			with tinysmtp.Connection.from_url(env['SMTP_URL']) as conn:
				message = tinysmtp.Message(
					sender = from_email,
					subject = "IUC: {} GB Threshold Reached".format(max_usage),
					recipients = [warn_email],
					body = "IUC checker reported current usage at: {} GB".format(usage),
				)
				conn.send(message)
				
				plugin.redis_set(warn_email_sent_key, 'true', ex = 2764800) # Expire after one month
		
	else:
		print "All good."

argparser = argh.ArghParser()
argparser.add_commands([run, check])

if __name__ == '__main__':
	argparser.dispatch(completion = False)
