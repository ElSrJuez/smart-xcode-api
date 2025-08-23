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
_API_PORT = config.get('api.apipxy', 'api_port', int)
_LOGGING_API_LOG_FILE = config.get('api.apipxy', 'logging_api_log_file')
_LOGGING_API_RAW_PATH = config.get('api.apipxy', 'logging_api_raw_path')
_LOGGING_API_DISCOVER_LOGS_PATH = config.get('api.apipxy', 'logging_api_discover_logs_path')
_FORCE_NON_GZIP = config.get('api.apipxy', 'fiddling_force_non_gzip', lambda v: v.lower() == 'true')
_OVERRIDE_CREDS = config.get('api.apipxy', 'override_creds', lambda v: v.lower() == 'true')
_LOGGING_PHASE = config.get('api.apipxy', 'logging_phase')

# Allowed methods must be set in config.ini; fail fast if missing
_ALLOWED_METHODS = [m.strip().upper() for m in config.get('api.apipxy', 'allowed_methods').split(',')]

app = FastAPI()

def log_transaction(request: Request, response: httpx.Response, req_body: bytes):
	try:
		req_headers = dict(request.headers)
		resp_headers = dict(response.headers)
		log_entry = {
			'timestamp': __import__('datetime').datetime.utcnow().isoformat() + 'Z',
			'request': {
				'method': request.method,
				'url': str(request.url),
				'headers': req_headers,
				'body': req_body.decode(errors='replace') if req_body else None
			},
			'response': {
				'status_code': response.status_code,
				'headers': resp_headers,
				'body': response.text
			}
		}
		# Add schema for discovery
		if 'discovery' in _LOGGING_API_LOG_FILE:
			log_entry['schema'] = {
				'request': list(log_entry['request'].keys()),
				'response': list(log_entry['response'].keys())
			}
		# Append to a single JSONL file for additive logging
		with open(_LOGGING_API_LOG_FILE, 'a', encoding='utf-8') as f:
			f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
	except Exception as e:
		logmod.log_message('error', f"Logging error: {e}")




@app.api_route('/{path:path}', methods=_ALLOWED_METHODS)
async def proxy(request: Request, path: str):
	method = request.method.upper()
	if method not in _ALLOWED_METHODS:
		logmod.log_message('warning', f"Blocked disallowed method: {method} for path: {path}")
		return Response(content="Method not allowed", status_code=405)

	url = f"{_BACKEND_URL}/{path}"
	headers = dict(request.headers)
	headers.pop('host', None)
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
	except httpx.RequestError as exc:
		logmod.log_message('error', f"Request error: {exc} | Request: {method} {url} | Params: {params} | Headers: {headers} | Body: {body[:200] if body else None}")
		return Response(content="Backend error", status_code=502)

	if resp.status_code >= 400:
		logmod.log_message('error', f"Backend error {resp.status_code}: {resp.text[:500]} | Request: {method} {url} | Params: {params} | Headers: {headers} | Body: {body[:200] if body else None}")

	log_transaction(request, resp, body)
	return Response(content=resp.content, status_code=resp.status_code, headers=dict(resp.headers))

if __name__ == "__main__":
	import sys
	_HOST = config.get('app', 'host')
	port = _API_PORT if len(sys.argv) == 1 else int(sys.argv[1])
	uvicorn.run("api.apipxy:app", host=_HOST, port=port, reload=True)