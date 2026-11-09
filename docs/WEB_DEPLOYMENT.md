# Hawkeye Jobs — personal web deployment

This deployment runs the existing Python job-search engine behind a single personal password. It does not create user accounts, registration, subscriptions or multiple workspaces. The desktop and terminal modes remain available.

## What this setup includes

- The existing FastAPI app, job database, search settings, history and automatic-search scheduler.
- A single password-protected browser session, with a signed HttpOnly cookie, 12-hour expiry and login-attempt throttling.
- Arabic/English interface and a Progressive Web App manifest/service worker for adding the site to a phone's home screen.
- A Python 3.12 container with Chromium running under Xvfb for the existing browser-based sources.
- A persistent host folder at `./hawkeye-data`; it is not stored inside the disposable container filesystem.

The app remains a single process with a SQLite database. Run one app container only; do not scale this SQLite-backed instance horizontally. Automatic searches run while this host is running. They cannot run while the PC/server is powered off.

## 1. Prepare the server

Install Docker Engine and the Docker Compose plugin on an always-on Linux machine, NAS or server. The browser UI can then be opened from your phone or computer. The host machine must remain online for scheduled searches and remote access.

Clone your repository and check out the development branch:

```bash
git clone https://github.com/qawadq/hawkeye-jobs.git
cd hawkeye-jobs
git checkout feat/personal-web-platform
```

Create the private environment file:

```bash
cp .env.web.example .env.web
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Edit `.env.web` and replace both placeholder values:
- `HAWKEYE_WEB_PASSWORD`: your own long password (at least 12 characters).
- `HAWKEYE_WEB_SESSION_SECRET`: the random value generated above (at least 32 characters).

For a first local test, keep:
- `HAWKEYE_ALLOWED_HOSTS=localhost,127.0.0.1`
- `HAWKEYE_COOKIE_SECURE=false` (only because the local test URL uses HTTP).

Do not commit `.env.web`. It is ignored by Git.

## 2. Start locally

```bash
docker compose up -d --build
docker compose logs -f hawkeye
```

Open `http://localhost:8765` on the host computer and enter the password. The container publishes its port only on the host's loopback interface; it is not directly exposed to the Internet.

The persistent database, settings and log files are stored in `./hawkeye-data`. Restarting or recreating the container does not remove this bind-mounted folder.

## 3. Publish securely through Cloudflare Tunnel

For remote access, use a **named Cloudflare Tunnel** and a hostname you control. The hostname must be routed to the service `http://hawkeye:8000` from the tunnel container.

1. Add your domain to Cloudflare and configure its DNS.
2. Create a named Tunnel in the Cloudflare dashboard and add a public hostname route to `http://hawkeye:8000`.
3. Copy the tunnel token into `CLOUDFLARE_TUNNEL_TOKEN` in `.env.web`.
4. Add the exact public hostname to `HAWKEYE_ALLOWED_HOSTS`, keeping `localhost,127.0.0.1` for the container health check.
5. Set `HAWKEYE_COOKIE_SECURE=true`.
6. Start the tunnel profile:

```bash
docker compose --profile tunnel up -d
docker compose logs -f cloudflared
```

The tunnel container is optional and is not started by the default local command. Never expose port 8000 directly to the public Internet; use HTTPS through the named tunnel or another correctly configured HTTPS reverse proxy.

The Cloudflare account inspected while preparing this branch currently has no zones/domains attached, so a stable public hostname cannot be configured from that account yet. The named-tunnel step therefore remains a manual deployment step after a domain is added.

## 4. Install on your phone

Open the HTTPS hostname in Chrome on Android, then use the browser menu and choose **Install app** or **Add to Home screen**. The app opens in a standalone window. Its service worker caches only static UI files; API responses, job records, login data and other personal content are never added to the offline cache.

The live search-progress stream uses Server-Sent Events. Use a normal named Tunnel or another proxy that supports long-lived streaming connections.

## 5. Back up your data

Stop the app before copying the SQLite data folder:

```bash
docker compose stop hawkeye
tar -czf hawkeye-data-backup-$(date +%F).tar.gz hawkeye-data
docker compose start hawkeye
```

Store the backup somewhere separate from the server. The folder contains your jobs, saved search settings and logs. Do not share it publicly.

- `docker compose down` stops and removes containers but keeps `./hawkeye-data`.
- Do not delete `./hawkeye-data` unless you intend to erase your saved jobs and settings.
- Keep only one running Hawkeye Jobs container because the current SQLite store and run lock are designed for a single local process.

## Known limits

- LinkedIn, Indeed, Bayt, NaukriGulf and Google Jobs are still subject to each site's availability, anti-bot controls and regional coverage. No scraping service can guarantee results from every source at all times.
- Cloudflare Tunnel does not host the Python job-search process; the Docker host must remain online.
- Browser notifications and background push notifications are not included in this first hosted foundation. Live updates appear while the web app is open; the database keeps results for the next visit.
- AI/CV tools and richer alert delivery can be added in later increments without changing the single-user model.
