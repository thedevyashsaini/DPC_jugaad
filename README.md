# Clipboard Fleet

Centralized multi-device clipboard architecture using Cloudflare Workers + Durable Objects, with a local Python agent CLI named `abc`.

## Architecture

- **Central hub**: `worker.js` (Cloudflare Worker + Durable Object `ClipboardHub`)
  - Stores joined devices and clipboard state in Durable Object storage.
  - Issues one-time join tokens via admin API.
  - Accepts websocket connections from agents and dashboard.
  - Routes clipboard updates both ways (agent -> hub -> dashboard, dashboard -> hub -> agent).
- **Dashboard UI**: served at `/` from the Worker
  - Shows joined device list.
  - Lets admin select a device, see latest clipboard, and send clipboard text.
  - Generates join command (`abc join --server ... --token ...`) after creating token.
- **Local agent CLI**: `clipcli.py`
  - `abc add <name>` creates token (admin side).
  - `abc join` joins a machine using token and saves credentials.
  - `abc run` runs clipboard sync agent in background/foreground.

## Why this architecture

- No external DB required: Durable Object storage is enough for fleet metadata and last clipboard content.
- Real-time updates: websockets for both agents and dashboard.
- Controlled onboarding: one-time expiring token per join.
- Easy hosting: deploy Worker on Cloudflare.

## Cloudflare setup

1. Install Wrangler (Node environment):

```bash
npm install -g wrangler
```

2. Login:

```bash
wrangler login
```

3. Set admin token secret (used by dashboard and `abc add`):

```bash
wrangler secret put ADMIN_TOKEN
```

4. Deploy:

```bash
wrangler deploy
```

The worker URL will be your central server URL.

## Python CLI setup (with uv)

```powershell
uv sync
```

This installs the `abc` script from `pyproject.toml`.

## Usage flow

### 1) Create join token (admin)

```powershell
uv run abc add "Dev-Laptop" --server https://your-worker-url.workers.dev --admin-token <ADMIN_TOKEN>
```

Output includes a join command with one-time token.

### 2) Join device

Run on target machine:

```powershell
uv run abc join --server https://your-worker-url.workers.dev --token <TOKEN>
```

Credentials are stored locally at:

`~/.clipboard_fleet/device.json`

### 3) Start agent

```powershell
uv run abc run
```

Now machine clipboard syncs with central hub.

### 4) Open dashboard

Visit worker URL in browser (`/`).
Paste admin token, connect, select device, and send clipboard text.

## API summary

- `POST /api/admin/create-token` (admin auth)
- `GET /api/admin/devices` (admin auth)
- `POST /api/admin/devices/:id/send` (admin auth)
- `POST /api/agent/join` (join token)
- `GET /ws/agent` (websocket, device credentials)
- `GET /ws/dashboard` (websocket, admin token)

## Security notes

- Protect `ADMIN_TOKEN` strongly; it controls onboarding and device clipboard writes.
- Join tokens are one-time and expiring.
- For production hardening, add:
  - per-device revocation API,
  - clipboard size limits,
  - audit logs,
  - optional encryption-at-rest strategy for clipboard payloads.
