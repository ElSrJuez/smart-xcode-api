from utils.discovery import parse_xc, ingest_object
from utils.dbops import get_category_for_action
# This is a simple API reverse proxy based on FastAPI.
# Main design parameters are transparency and simplicity.
# Main objective is to have simple, robust object logging that retains the transactions' native schema.



import os
import json
from fastapi import FastAPI, Request, Response
import httpx
import uvicorn
from utils import config, logging as logmod


# Preload all config values needed for this module, matching config.ini
_BACKEND_URL = config.get('api.apipxy', 'target_url')
_BACKEND_USERNAME = config.get('api.apipxy', 'target_username')
_BACKEND_PASSWORD = config.get('api.apipxy', 'target_password')
_API_HOST = config.get('app', 'host')
_API_PORT = config.get('api.apipxy', 'api_port', int)
_LOGGING_API_LOG_FILE = config.get('api.apipxy', 'logging_api_log_file')
_LOGGING_API_RAW_PATH = config.get('api.apipxy', 'logging_api_raw_path')
_LOGGING_API_DISCOVER_JSONL_PATH = config.get('api.apipxy', 'logging_api_discover_jsonl_path')
_LOGGING_API_DISCOVER_JSONL_ENABLED = config.get('api.apipxy', 'logging_api_discover_jsonl_enabled', lambda v: v.lower() == 'true')
_FORCE_NON_GZIP = config.get('api.apipxy', 'fiddling_force_non_gzip', lambda v: v.lower() == 'true')
_OVERRIDE_CREDS = config.get('api.apipxy', 'override_creds', lambda v: v.lower() == 'true')
_LOGGING_PHASE = config.get('api.apipxy', 'logging_phase')

# Allowed methods must be set in config.ini; fail fast if missing
_ALLOWED_METHODS = [m.strip().upper() for m in config.get('api.apipxy', 'allowed_methods').split(',')]

# Maintenance lock file path (semaphore for maintenance mode)
_MAINTENANCE_LOCK_PATH = config.get('app', 'maintenance_flag_filename')
app = FastAPI()



def is_maintenance_mode():
    """
    Returns True if the maintenance lock file exists, else False.
    Uses the preloaded _MAINTENANCE_LOCK_PATH.
    """
    return os.path.exists(_MAINTENANCE_LOCK_PATH)

def log_transaction(request: Request, response: httpx.Response, req_body: bytes):
	try:
		from datetime import datetime
		req_headers = dict(request.headers)
		resp_headers = dict(response.headers)
		# Always build the full request URL with query params
		from urllib.parse import urlencode
		url = str(request.url)
		# Compose summary log entry (no payloads)
		summary_entry = {
			'timestamp': datetime.utcnow().isoformat() + 'Z',
			'method': request.method,
			'url': url,
			'status_code': response.status_code,
			'request_headers': req_headers,
			'response_headers': resp_headers
		}
		# Determine log level for minimal summary
		import logging
		log_level = logging.getLevelName(logmod._get_logger().level)
		if log_level == 'INFO':
			# Minimal summary: just method, url, status
			logmod.log_message('info', f"{request.method} {url} {response.status_code}")
		else:
			# Full summary (still no payloads)
			logmod.log_message('debug',
				"{method} {url} {status_code} | req_headers={req_headers} resp_headers={resp_headers}".format(
					method=request.method,
					url=url,
					status_code=response.status_code,
					req_headers=json.dumps(req_headers, ensure_ascii=False),
					resp_headers=json.dumps(resp_headers, ensure_ascii=False)
				)
			)
		# JSONL payload logging if enabled
		if _LOGGING_API_DISCOVER_JSONL_ENABLED:
			jsonl_entry = {
				'timestamp': datetime.utcnow().isoformat() + 'Z',
				'request': {
					'method': request.method,
					'url': url,
					'headers': req_headers,
					'body': req_body.decode(errors='replace') if req_body else None
				},
				'response': {
					'status_code': response.status_code,
					'headers': resp_headers,
					'body': response.text
				}
			}
			# Write to JSONL file in discovery path
			jsonl_path = os.path.join(_LOGGING_API_DISCOVER_JSONL_PATH, 'discovery.jsonl')
			os.makedirs(os.path.dirname(jsonl_path), exist_ok=True)
			with open(jsonl_path, 'a', encoding='utf-8') as f:
				f.write(json.dumps(jsonl_entry, ensure_ascii=False) + '\n')
	except Exception as e:
		logmod.log_message('error', f"Logging error: {e}")




@app.api_route('/{path:path}', methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
async def proxy(request: Request, path: str):
	method = request.method.upper()
	if method not in _ALLOWED_METHODS:
		logmod.log_message('warning', f"Blocked disallowed method: {method} for path: {path}")
		return Response(content="Method not allowed", status_code=405)

	url = f"{_BACKEND_URL}/{path}"
	headers = dict(request.headers)
	headers.pop('host', None)
	if _FORCE_NON_GZIP:
		headers['accept-encoding'] = 'identity'
	body = await request.body()

	params = dict(request.query_params)
	if _OVERRIDE_CREDS:
		params['username'] = _BACKEND_USERNAME
		params['password'] = _BACKEND_PASSWORD
	else:
		params.setdefault('username', _BACKEND_USERNAME)
		params.setdefault('password', _BACKEND_PASSWORD)

	try:
		async with httpx.AsyncClient() as client:
			resp = await client.request(
				method,
				url,
				headers=headers,
				params=params,
				content=body,
				timeout=30.0
			)
		# Event-driven discovery ingestion for XC API using schema-driven mapping
		action = params.get('action', '').lower()
		if resp.status_code == 200 and resp.headers.get('content-type', '').startswith('application/json'):
			try:
				data = resp.json()
			except Exception as e:
				logmod.log_message('error', f"Failed to parse JSON for discovery ingestion: {e}")
				data = None
			category = get_category_for_action(action)
			if data and category:
				try:
					discovered = list(parse_xc(data, category=category))
					count = 0
					for obj in discovered:
						try:
							ingest_object(category, obj)
							count += 1
						except Exception as e:
							logmod.log_message('error', f"Failed to ingest object in {category}: {e} | obj={obj}")
					logmod.log_message('info', f"Discovery ingestion complete for action={action}: {count} objects ingested.")
				except Exception as e:
					logmod.log_message('error', f"Discovery ingestion failed for action={action}: {e}")
	except httpx.RequestError as exc:
		import collections.abc
		def format_exc_chain(e):
			chain = []
			visited = set()
			def walk(ex):
				if id(ex) in visited:
					return
				visited.add(id(ex))
				etype = type(ex).__name__
				msg = str(ex)
				chain.append(f"[{etype}] {msg}")
				# ExceptionGroup (Python 3.11+)
				if hasattr(ex, 'exceptions') and isinstance(getattr(ex, 'exceptions'), collections.abc.Sequence):
					for sub in ex.exceptions:
						walk(sub)
				else:
					cause = getattr(ex, '__cause__', None)
					context = getattr(ex, '__context__', None)
					if cause:
						walk(cause)
					elif context:
						walk(context)
			walk(e)
			return ' -> '.join(chain)
		full_exc = format_exc_chain(exc)
		# Build the full URL with query params for logging
		from urllib.parse import urlencode
		full_url = url
		if params:
			full_url += '?' + urlencode(params)
		logmod.log_message(
			'error',
			f"Request error chain: {full_exc} | {method} {full_url} | req_headers={headers} req_body={body[:200] if body else None}"
		)
		return Response(content="Backend error", status_code=502)

	if resp.status_code >= 400:
		# Error log: summary only, no payloads
		from urllib.parse import urlencode
		full_url = url
		if params:
			full_url += '?' + urlencode(params)
		logmod.log_message('error',
			"Backend error {status_code} | {method} {full_url} | req_headers={headers}".format(
				status_code=resp.status_code,
				method=method,
				full_url=full_url,
				headers=json.dumps(headers, ensure_ascii=False)
			)
		)

	log_transaction(request, resp, body)
	return Response(content=resp.content, status_code=resp.status_code, headers=dict(resp.headers))

if __name__ == "__main__":
	import sys
	# No in-code defaults: require api_host and api_port in config.ini
	host = _API_HOST
	port = _API_PORT
	if len(sys.argv) == 2:
		port = int(sys.argv[1])
	elif len(sys.argv) == 3:
		host = sys.argv[1]
		port = int(sys.argv[2])
	uvicorn.run("api.apipxy:app", host=host, port=int(port))