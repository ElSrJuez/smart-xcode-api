# This is a simple API reverse proxy based on FastAPI.
# Main design parameters are transparency and simplicity.
# Main objective is to have simple, robust object logging that retains the transactions' native schema.


import configparser
import logging
import os
import json
from fastapi import FastAPI, Request, Response
import httpx
import uvicorn

# Read backend config from config.ini
config = configparser.ConfigParser()
config.read('config.ini')
backend_url = config.get('XTREAM CODES api', 'iptv_url')
backend_username = config.get('XTREAM CODES api', 'iptv_username')
backend_password = config.get('XTREAM CODES api', 'iptv_password')
logging_phase = config.get('log', 'logging_phase', fallback='raw').lower()


# Read force_non_gzip from [fiddling] section
force_non_gzip = False
if config.has_section('fiddling'):
	force_non_gzip = config.getboolean('fiddling', 'force_non_gzip', fallback=False)

# Read override_creds from [auth] section
override_creds = False
if config.has_section('auth'):
	override_creds = config.getboolean('auth', 'override_creds', fallback=False)


# Set up logging directories
LOG_DIR = os.path.join(os.path.dirname(__file__), 'log', logging_phase)
os.makedirs(LOG_DIR, exist_ok=True)
TROUBLESHOOT_DIR = os.path.join(os.path.dirname(__file__), 'log', 'troubleshooting')
os.makedirs(TROUBLESHOOT_DIR, exist_ok=True)

# Set up troubleshooting logger
troubleshooting_log_file = os.path.join(TROUBLESHOOT_DIR, 'troubleshooting.log')
troubleshooting_logger = logging.getLogger('troubleshooting')
troubleshooting_logger.setLevel(logging.INFO)
if not troubleshooting_logger.handlers:
	handler = logging.FileHandler(troubleshooting_log_file, encoding='utf-8')
	formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
	handler.setFormatter(formatter)
	troubleshooting_logger.addHandler(handler)

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
		if logging_phase == 'discovery':
			log_entry['schema'] = {
				'request': list(log_entry['request'].keys()),
				'response': list(log_entry['response'].keys())
			}
		# Append to a single JSONL file for additive logging
		log_file = os.path.join(LOG_DIR, 'discovery.jsonl')
		with open(log_file, 'a', encoding='utf-8') as f:
			f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
	except Exception as e:
		logging.error(f"Logging error: {e}")



@app.api_route('/{path:path}', methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
async def proxy(request: Request, path: str):
	url = f"{backend_url}/{path}"
	method = request.method
	headers = dict(request.headers)
	headers.pop('host', None)
	body = await request.body()

	params = dict(request.query_params)
	if override_creds:
		# Always override username and password
		params['username'] = backend_username
		params['password'] = backend_password
	else:
		params.setdefault('username', backend_username)
		params.setdefault('password', backend_password)

	async with httpx.AsyncClient() as client:
		try:
			resp = await client.request(
				method,
				url,
				headers=headers,
				params=params,
				content=body,
				timeout=30.0
			)
		except httpx.RequestError as exc:
			troubleshooting_logger.error(f"Request error: {exc}\nRequest: {method} {url}\nParams: {params}\nHeaders: {headers}\nBody: {body[:200] if body else None}")
			return Response(content="Backend error", status_code=502)

	# Log backend errors (status >= 400) to troubleshooting log
	if resp.status_code >= 400:
		troubleshooting_logger.error(f"Backend error {resp.status_code}: {resp.text[:500]}\nRequest: {method} {url}\nParams: {params}\nHeaders: {headers}\nBody: {body[:200] if body else None}")

	log_transaction(request, resp, body)
	return Response(content=resp.content, status_code=resp.status_code, headers=dict(resp.headers))

if __name__ == "__main__":
	uvicorn.run("apipxy:app", host="0.0.0.0", port=8000, reload=True)