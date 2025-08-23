# HOWTO: Running smart-xcode-api

Follow these steps to set up and run the smart-xcode-api reverse proxy solution:

## 1. Clone the Repository

```
git clone https://github.com/ElSrJuez/smart-xcode-api.git
cd smart-xcode-api
```

## 2. Set Up Python Environment

It is recommended to use a virtual environment:

```
python -m venv .venv
.venv\Scripts\activate  # On Windows
# Or
source .venv/bin/activate  # On Linux/macOS
```

## 3. Install Requirements

```
pip install -r requirements.txt
```

## 4. Configure Backend Credentials

- Copy `config.ini.sample` to `config.ini`.
- Edit `config.ini` and fill in your IPTV backend URL, username, and password.

## 5. Run the Proxy Server

```
uvicorn apipxy:app --reload
```

- The server will start on `http://127.0.0.1:8000` by default.

## 6. Configure Your IPTV Client

- Use the proxy URL (e.g., `http://127.0.0.1:8000`) in your IPTV client.
- No credentials are needed on the client side; the proxy injects them.

## 7. Monitor Logs and Database

- Logs are stored in the `log/` directory.
- The minimalist database is stored in the `db/` directory.

## 8. Stopping the Server

- Press `Ctrl+C` in the terminal to stop the server.

## 9. (Optional) Customization

- Adjust logging phases or other settings in `config.ini` as needed.
- Explore and extend the codebase for custom features.

---

For troubleshooting or advanced usage, see the `README.md` and code comments.
