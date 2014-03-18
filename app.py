from flask import Flask, request, Response
from iuc import get_plugin_by_conf_string, default_conf_string


app = Flask(__name__)

def get_plugin():
	conf_string = request.args.get('conf', default_conf_string)
	return get_plugin_by_conf_string(conf_string)

@app.route('/')
def combined_usage():
	plugin = get_plugin()
	
	try:
		body = str(plugin.combined_usage)
	except plugin.EndpointOffline:
		return "Endpoint Offline :/"
	
	if plugin.usage_cap:
		body += ' ' + plugin.usage_percentage
	
	if plugin.data_last_retrieved:
		body += '\n\nData Last Retrieved: ' + plugin.data_last_retrieved.strftime('%c')
		
	return Response(body, content_type = "text/plain")

@app.route('/stats')
def stats():
	plugin = get_plugin()
	
	body = 'Was Online: ' + (plugin.redis_get('was_online') or '0')
	body += '\nWas Offline: ' + (plugin.redis_get('was_offline') or '0')
	
	if plugin.data_last_retrieved:
		body += '\nData Last Retrieved: ' + plugin.data_last_retrieved.strftime('%c')
	
	return Response(body, content_type = "text/plain")
