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
_DISCOVER_JSONL_PATH = config.get('api.apipxy', 'logging_api_discover_jsonl_path')
_DISCOVER_JSONL_ENABLED = config.get('api.apipxy', 'logging_api_discover_jsonl_enabled', lambda v: v.lower() == 'true')
_FORCE_NON_GZIP = config.get('api.apipxy', 'fiddling_force_non_gzip', lambda v: v.lower() == 'true')
_OVERRIDE_CREDS = config.get('api.apipxy', 'override_creds', lambda v: v.lower() == 'true')
_LOGGING_PHASE = config.get('api.apipxy', 'logging_phase')

# Allowed methods must be set in config.ini; fail fast if missing
_ALLOWED_METHODS = [m.strip().upper() for m in config.get('api.apipxy', 'allowed_methods').split(',')]

# JSONL transaction logging for payloads (not full HTTP transaction)
def log_jsonl_payload(payload: dict):
	"""
	Log the payload of a transaction as a JSONL object for troubleshooting/manual analysis.
	Uses preloaded config variables only.
	"""
	if not _DISCOVER_JSONL_ENABLED:
		return
	try:
		os.makedirs(_DISCOVER_JSONL_PATH, exist_ok=True)
		log_file = os.path.join(_DISCOVER_JSONL_PATH, 'discovery.jsonl')
		entry = dict(payload)
		entry['logged_at'] = __import__('datetime').datetime.utcnow().isoformat() + 'Z'
		with open(log_file, 'a', encoding='utf-8') as f:
			f.write(json.dumps(entry, ensure_ascii=False) + '\n')
	except Exception as e:
		logmod.log_message('error', f"JSONL logging error: {e}")

app = FastAPI()

def log_transaction(request: Request, response: httpx.Response, req_body: bytes):
	try:
			from utils import config as _log_config
			log_level = _log_config.get('app', 'logging_common_level', str).upper()
			# If DEBUG, log full URL with query string and all details
			if log_level == 'DEBUG':
				full_url = str(response.request.url) if hasattr(response, 'request') and hasattr(response.request, 'url') else str(request.url)
				logmod.log_message(
					'debug',
					f"[apipxy] {request.method} {full_url} status={response.status_code} req_headers={dict(request.headers)} req_body={req_body.decode(errors='replace') if req_body else None} resp_headers={dict(response.headers)} resp_body={response.text}"
				)
			else:
				# Minimal log for non-debug
				logmod.log_message(
					'info',
					f"[apipxy] {request.method} {request.url} status={response.status_code}"
				)
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
		from utils import config as _log_config
		log_level = _log_config.get('app', 'logging_common_level', str).upper()
		# Log full details in DEBUG, minimal otherwise
		if log_level == 'DEBUG':
			# Reconstruct full URL with query string
			import urllib.parse
			full_url = url
			if params:
				full_url = f"{url}?{urllib.parse.urlencode(params)}"
			req_body_str = body.decode(errors='replace') if body else None
			logmod.log_message(
				'error',
				f"[apipxy] Request error: {exc} | {method} {full_url} req_headers={headers} req_body={req_body_str}"
			)
		else:
			logmod.log_message('error', f"[apipxy] Request error: {exc} | {method} {url}")
		return Response(content="Backend error", status_code=502)

		if resp.status_code >= 400:
			logmod.log_message('error', f"[apipxy] Backend error {resp.status_code}: {method} {url}")

	# Passive JSONL transaction logging: log only the backend payload, not the full HTTP transaction
	# Only log if enabled and response is JSON or text (not for every request blindly)
		content_type = resp.headers.get('content-type', '')
		if _DISCOVER_JSONL_ENABLED and ('json' in content_type or 'text' in content_type):
			try:
				payload = resp.json()
			except Exception:
				payload = {"raw_body": resp.text}
			log_jsonl_payload(payload)

		log_transaction(request, resp, body)
		return Response(content=resp.content, status_code=resp.status_code, headers=dict(resp.headers))

if __name__ == "__main__":
		import sys
		_HOST = config.get('app', 'host')
		port = int(_API_PORT) if len(sys.argv) == 1 else int(sys.argv[1])
		uvicorn.run("api.apipxy:app", host=_HOST, port=port, reload=True)