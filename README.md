# Xcode Reverse Proxy: Modern IPTV API Discovery & Management

![Status](https://img.shields.io/badge/status-active-brightgreen)
![Python](https://img.shields.io/badge/python-3.8%2B-blue)

> **A modern, minimalist, and extensible reverse proxy for Xtream Codes IPTV APIs.**
> 
> - Effortless client setup (no credentials needed)
> - Real-time passive discovery of categories, channels, streams, EPG, and more
> - Hierarchical, schema-driven database for advanced moderation and analytics
> - Designed for the IPTV community: transparency, simplicity, and power

---

## 🚀 Quick Start

1. **Clone the repo:**
   ```sh
   git clone https://github.com/ElSrJuez/smart-xcode-api.git
   cd smart-xcode-api
   ```
2. **Configure:**
   - Edit `config.ini` with your backend xcode API URL and credentials.
3. **Run (Docker, recommended):**
   ```sh
   docker build -t smart-xcode-api .
   docker run -p 8000:8000 -p 5001:5001 \
     -v $PWD/db:/app/db -v $PWD/log:/app/log \
     smart-xcode-api
   ```
   - Both the proxy (FastAPI) and admin UI (Flask) run in a single container.
   - Access the proxy at `http://localhost:8000/` and the admin UI at `http://localhost:5001/`.

---

## 🌟 Features

- **Credential-Free Client Access:**
  - Clients connect using a simple, short URL—no credentials required.
  - The proxy injects backend credentials for all xcode API requests.
- **Passive API Discovery:**
  - Monitors and logs all xcode API, M3U, and EPG transactions.
  - Automatically discovers and catalogs categories, channels, streams, EPG, and more.
- **Modern Admin UI:**
  - Hierarchical, schema-driven view of all discovered objects.
  - One-click enable/disable for categories, channels, streams.
  - Smart tag management and real-time statistics.
  - Maintenance mode toggle (pauses proxy for safe admin edits).
- **Minimalist, Extensible Database:**
  - Lightweight, hierarchical storage (TinyDB or similar).
  - Preserves original schema, tracks `added` and `last_seen`.
- **Comprehensive Logging:**
  - Structured, additive logs for discovery and troubleshooting.
- **Easy Deployment:**
  - Single Docker container, no external dependencies, no process supervisor needed.

---

## 📺 For the IPTV Community

- **Open, transparent, and community-driven.**
- **No vendor lock-in, no hidden logic.**
- **Actively maintained and welcoming to contributors!**
- **Perfect for power users and IPTV enthusiasts who want control and insight.**

---

## 🛠️ Project Structure

- `apipxy.py` — Main FastAPI proxy and discovery logic
- `admin/` — Flask-based admin UI
- `config.ini` — Configuration
- `db/` — Hierarchical database (TinyDB, JSON, etc.)
- `log/` — Discovery and troubleshooting logs
- `README.md` — Project documentation

---

## 📦 Deployment Details

- **Single Docker Container:**
  - Both proxy and admin UI run together for simplicity.
  - Launch script or Docker CMD starts both processes.
  - Restart the container if anything crashes.
  - Shared volumes for `db/` and `log/`.
- **Requirements:**
  - All requirements from `requirements.txt`, `admin/requirements.txt`, `api/requirements.txt`, and `utils/requirements.txt` are installed in the Docker image.
- **No Process Supervisor:**
  - Simplicity first—let Docker handle restarts.

---

## 🗺️ Roadmap / TODO

- [ ] Add a Dockerfile and launch script to run both proxy and admin in a single container.
- [ ] Ensure all requirements files are installed in the Docker build.
- [ ] Document the Docker build and run process in this README.
- [ ] (Optional) Add log rotation or separation if needed for clarity.
- [ ] Invite feedback and contributions from the IPTV community!

---

## License

MIT License

## Credits

Created by github.com/ElSrJuez

