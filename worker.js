const DASHBOARD_HTML = `<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Clipboard Fleet</title>
    <style>
      :root {
        --bg: #f5f1e8;
        --paper: #fffdf8;
        --ink: #1d1a15;
        --muted: #70675d;
        --line: #e2d9ca;
        --brand: #ff5a36;
        --brand2: #ffca42;
        --ok: #1c8f4d;
        --err: #c92a2a;
      }
      * { box-sizing: border-box; }
      body {
        margin: 0;
        min-height: 100vh;
        font-family: "Plus Jakarta Sans", "Segoe UI", sans-serif;
        background:
          radial-gradient(800px 400px at 100% -10%, rgba(255, 90, 54, 0.18), transparent 70%),
          radial-gradient(700px 300px at 0% 0%, rgba(255, 202, 66, 0.22), transparent 70%),
          var(--bg);
        color: var(--ink);
        padding: 16px;
      }
      .app {
        max-width: 1320px;
        margin: 0 auto;
        border: 1px solid var(--line);
        border-radius: 20px;
        overflow: hidden;
        background: rgba(255, 255, 255, 0.8);
        backdrop-filter: blur(8px);
      }
      .top {
        padding: 16px 18px;
        border-bottom: 1px solid var(--line);
        display: flex;
        justify-content: space-between;
        gap: 14px;
        align-items: center;
      }
      .title {
        margin: 0;
        font-size: clamp(22px, 3vw, 34px);
        letter-spacing: -0.02em;
      }
      .sub { margin: 4px 0 0; color: var(--muted); font-size: 13px; }
      .badge {
        font-size: 12px;
        border: 1px solid #ffd7ce;
        border-radius: 999px;
        background: linear-gradient(120deg, #ffe8e2, #fff3cf);
        padding: 8px 12px;
      }
      .grid {
        display: grid;
        grid-template-columns: minmax(290px, 380px) 1fr;
        min-height: calc(100vh - 140px);
      }
      .left { border-right: 1px solid var(--line); padding: 16px; }
      .right { padding: 16px; }
      .row {
        display: flex;
        gap: 8px;
        align-items: center;
        margin-bottom: 10px;
        flex-wrap: wrap;
      }
      input, textarea, select {
        width: 100%;
        border: 1px solid var(--line);
        border-radius: 10px;
        padding: 10px;
        background: var(--paper);
        font: inherit;
      }
      textarea { min-height: 170px; resize: vertical; }
      button {
        border: 0;
        border-radius: 10px;
        padding: 10px 12px;
        font: inherit;
        font-weight: 700;
        cursor: pointer;
        background: linear-gradient(120deg, var(--brand), var(--brand2));
        color: #2f1900;
      }
      button.ghost {
        border: 1px solid var(--line);
        background: var(--paper);
        color: var(--ink);
      }
      .eyebrow {
        margin: 10px 0 8px;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        font-size: 11px;
        color: var(--muted);
        font-weight: 700;
      }
      .list {
        border: 1px solid var(--line);
        border-radius: 12px;
        background: rgba(255, 255, 255, 0.78);
        max-height: calc(100vh - 350px);
        min-height: 240px;
        overflow: auto;
        padding: 8px;
      }
      .device {
        width: 100%;
        text-align: left;
        border: 1px solid transparent;
        border-radius: 10px;
        background: #fff;
        padding: 10px;
        margin-bottom: 8px;
        cursor: pointer;
      }
      .device.active { border-color: #ffab99; background: #fff7f4; }
      .meta { font-size: 12px; color: var(--muted); margin-top: 6px; }
      .ok { color: var(--ok); }
      .err { color: var(--err); }
      pre {
        background: #191714;
        color: #fff4d4;
        border-radius: 10px;
        padding: 10px;
        overflow: auto;
      }
      .status { font-size: 13px; color: var(--muted); }
      .clip {
        border: 1px solid var(--line);
        border-radius: 10px;
        min-height: 170px;
        padding: 12px;
        white-space: pre-wrap;
        background: rgba(255, 255, 255, 0.72);
      }
      @media (max-width: 980px) {
        .grid { grid-template-columns: 1fr; min-height: auto; }
        .left { border-right: 0; border-bottom: 1px solid var(--line); }
      }
    </style>
  </head>
  <body>
    <main class="app">
      <header class="top">
        <div>
          <h1 class="title">Clipboard Fleet</h1>
          <p class="sub">Central hub for all joined machine clipboards</p>
        </div>
        <div class="badge" id="badge">Disconnected</div>
      </header>

      <section class="grid">
        <aside class="left">
          <p class="eyebrow">Auth</p>
          <div class="row">
            <input id="adminToken" placeholder="Admin token" />
          </div>
          <div class="row">
            <button id="connectBtn">Connect</button>
            <button class="ghost" id="refreshBtn">Refresh</button>
          </div>

          <p class="eyebrow">Create Join Command</p>
          <div class="row"><input id="nameInput" placeholder="Device name (eg. Dev-Laptop)" /></div>
          <div class="row"><input id="ttlInput" type="number" value="900" min="60" /></div>
          <div class="row"><button id="createTokenBtn">Generate Join Token</button></div>
          <pre id="joinCommand">No token generated yet</pre>

          <p class="eyebrow">Joined Devices</p>
          <div class="list" id="deviceList"></div>
        </aside>

        <section class="right">
          <p class="eyebrow">Selected Device Clipboard</p>
          <div class="clip" id="clipboardView">Select a device</div>
          <p class="eyebrow">Send To Selected Device</p>
          <textarea id="sendInput" placeholder="Type text to push into selected machine clipboard"></textarea>
          <div class="row">
            <button id="sendBtn">Send Clipboard</button>
            <span class="status" id="status">Ready</span>
          </div>
        </section>
      </section>
    </main>

    <script>
      const adminTokenInput = document.getElementById("adminToken");
      const connectBtn = document.getElementById("connectBtn");
      const refreshBtn = document.getElementById("refreshBtn");
      const createTokenBtn = document.getElementById("createTokenBtn");
      const nameInput = document.getElementById("nameInput");
      const ttlInput = document.getElementById("ttlInput");
      const joinCommand = document.getElementById("joinCommand");
      const deviceList = document.getElementById("deviceList");
      const clipboardView = document.getElementById("clipboardView");
      const sendInput = document.getElementById("sendInput");
      const sendBtn = document.getElementById("sendBtn");
      const statusEl = document.getElementById("status");
      const badge = document.getElementById("badge");

      let selectedDeviceId = null;
      let devices = [];
      let stream = null;

      const cachedToken = localStorage.getItem("clipboard_admin_token") || "";
      if (cachedToken) adminTokenInput.value = cachedToken;

      function setStatus(text, type) {
        statusEl.textContent = text;
        statusEl.className = "status " + (type || "");
      }

      function escapeHtml(value) {
        return (value || "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
      }

      function showDevices() {
        deviceList.innerHTML = "";
        if (!devices.length) {
          deviceList.innerHTML = '<div class="meta">No joined devices yet</div>';
          clipboardView.textContent = "No joined devices";
          return;
        }

        if (!selectedDeviceId) {
          selectedDeviceId = devices[0].id;
        }

        for (const device of devices) {
          const btn = document.createElement("button");
          btn.className = "device " + (device.id === selectedDeviceId ? "active" : "");
          btn.type = "button";
          btn.innerHTML =
            '<div><strong>' +
            escapeHtml(device.name) +
            '</strong></div>' +
            '<div class="meta">' +
            (device.connected ? "Online" : "Offline") +
            ' - Last seen ' +
            new Date(device.last_seen_at || 0).toLocaleString() +
            "</div>";
          btn.addEventListener("click", () => {
            selectedDeviceId = device.id;
            showDevices();
          });
          deviceList.appendChild(btn);
        }

        const selected = devices.find((d) => d.id === selectedDeviceId);
        clipboardView.textContent = selected ? selected.last_clipboard || "(empty clipboard)" : "Select a device";
      }

      async function authedFetch(path, init = {}) {
        const token = adminTokenInput.value.trim();
        if (!token) {
          throw new Error("Admin token required");
        }
        localStorage.setItem("clipboard_admin_token", token);
        const headers = new Headers(init.headers || {});
        headers.set("x-admin-token", token);
        return fetch(path, { ...init, headers });
      }

      async function refreshDevices() {
        try {
          const res = await authedFetch("/api/admin/devices");
          if (!res.ok) throw new Error("HTTP " + res.status);
          const data = await res.json();
          devices = data.devices || [];
          showDevices();
          setStatus("Loaded " + devices.length + " devices", "ok");
        } catch (err) {
          setStatus(err.message || "Unable to fetch devices", "err");
        }
      }

      async function createJoinToken() {
        try {
          const name = nameInput.value.trim();
          if (!name) throw new Error("Device name required");
          const ttl = Number(ttlInput.value || 900);
          const res = await authedFetch("/api/admin/create-token", {
            method: "POST",
            headers: { "content-type": "application/json" },
            body: JSON.stringify({ name, ttl_seconds: ttl }),
          });
          if (!res.ok) throw new Error("HTTP " + res.status);
          const data = await res.json();
          joinCommand.textContent = data.join_command;
          setStatus("Join command generated", "ok");
        } catch (err) {
          setStatus(err.message || "Token generation failed", "err");
        }
      }

      async function sendToDevice() {
        try {
          if (!selectedDeviceId) throw new Error("Select a device first");
          const text = sendInput.value;
          const res = await authedFetch("/api/admin/devices/" + encodeURIComponent(selectedDeviceId) + "/send", {
            method: "POST",
            headers: { "content-type": "application/json" },
            body: JSON.stringify({ text }),
          });
          if (!res.ok) throw new Error("HTTP " + res.status);
          setStatus("Clipboard pushed", "ok");
        } catch (err) {
          setStatus(err.message || "Send failed", "err");
        }
      }

      function connectEvents() {
        if (stream) {
          try { stream.close(); } catch {}
        }
        const token = adminTokenInput.value.trim();
        if (!token) return;

        const wsProto = location.protocol === "https:" ? "wss" : "ws";
        stream = new WebSocket(
          wsProto + "://" + location.host + "/ws/dashboard?admin_token=" + encodeURIComponent(token)
        );
        stream.onopen = () => {
          badge.textContent = "Live";
          setStatus("Live updates connected", "ok");
        };
        stream.onerror = () => {
          badge.textContent = "Reconnecting";
          setStatus("Live stream reconnecting", "err");
        };
        stream.onclose = () => {
          badge.textContent = "Disconnected";
          setTimeout(connectEvents, 1500);
        };
        stream.onmessage = (event) => {
          try {
            const msg = JSON.parse(event.data);
            if (msg.type === "devices") {
              devices = msg.devices || [];
              showDevices();
            }
          } catch {
            setStatus("Malformed stream event", "err");
          }
        };
      }

      connectBtn.addEventListener("click", async () => {
        await refreshDevices();
        connectEvents();
      });
      refreshBtn.addEventListener("click", refreshDevices);
      createTokenBtn.addEventListener("click", createJoinToken);
      sendBtn.addEventListener("click", sendToDevice);

      if (cachedToken) {
        refreshDevices();
        connectEvents();
      }
    </script>
  </body>
</html>`;

function jsonResponse(data, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: {
      "content-type": "application/json; charset=utf-8",
      "cache-control": "no-store",
    },
  });
}

async function readJson(request) {
  try {
    return await request.json();
  } catch {
    return null;
  }
}

function randomToken(bytes = 18) {
  const arr = new Uint8Array(bytes);
  crypto.getRandomValues(arr);
  return Array.from(arr, (x) => x.toString(16).padStart(2, "0")).join("");
}

function nowIso() {
  return new Date().toISOString();
}

function wsUrlFromHttp(url, path, params) {
  const u = new URL(path, url);
  u.protocol = u.protocol === "https:" ? "wss:" : "ws:";
  for (const [k, v] of Object.entries(params || {})) {
    u.searchParams.set(k, v);
  }
  return u.toString();
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (url.pathname === "/") {
      return new Response(DASHBOARD_HTML, {
        headers: {
          "content-type": "text/html; charset=utf-8",
          "cache-control": "no-store",
        },
      });
    }

    const id = env.CLIPBOARD_HUB.idFromName("global-fleet");
    const stub = env.CLIPBOARD_HUB.get(id);
    return stub.fetch(request);
  },
};

export class ClipboardHub {
  constructor(state, env) {
    this.state = state;
    this.env = env;
    this.agentSockets = new Map();
    this.dashboardSockets = new Set();

    for (const ws of this.state.getWebSockets()) {
      const meta = ws.deserializeAttachment();
      if (!meta || !meta.role) {
        continue;
      }
      if (meta.role === "agent" && meta.deviceId) {
        this.agentSockets.set(meta.deviceId, ws);
      }
      if (meta.role === "dashboard") {
        this.dashboardSockets.add(ws);
      }
    }
  }

  async fetch(request) {
    const url = new URL(request.url);
    const path = url.pathname;

    if (path === "/api/admin/create-token" && request.method === "POST") {
      return this.createJoinToken(request, url);
    }
    if (path === "/api/admin/devices" && request.method === "GET") {
      return this.listDevices(request);
    }
    if (path.startsWith("/api/admin/devices/") && path.endsWith("/send") && request.method === "POST") {
      return this.sendToDevice(request, path);
    }
    if (path === "/api/agent/join" && request.method === "POST") {
      return this.joinAgent(request, url);
    }
    if (path === "/ws/agent") {
      return this.acceptAgentSocket(request, url);
    }
    if (path === "/ws/dashboard") {
      return this.acceptDashboardSocket(request, url);
    }

    return jsonResponse({ error: "Not found" }, 404);
  }

  async verifyAdmin(request, url = null) {
    const headerToken = request.headers.get("x-admin-token") || "";
    const queryToken = url ? url.searchParams.get("admin_token") || "" : "";
    const token = headerToken || queryToken;
    if (!this.env.ADMIN_TOKEN || token !== this.env.ADMIN_TOKEN) {
      return false;
    }
    return true;
  }

  async getDevicesMap() {
    return (await this.state.storage.get("devices")) || {};
  }

  async setDevicesMap(devices) {
    await this.state.storage.put("devices", devices);
  }

  async setJoinToken(token, data) {
    await this.state.storage.put(`join:${token}`, data);
  }

  async getJoinToken(token) {
    return this.state.storage.get(`join:${token}`);
  }

  async createJoinToken(request, url) {
    if (!(await this.verifyAdmin(request))) {
      return jsonResponse({ error: "Unauthorized" }, 401);
    }

    const body = await readJson(request);
    if (!body || typeof body.name !== "string" || !body.name.trim()) {
      return jsonResponse({ error: "name is required" }, 400);
    }

    const ttl = Number(body.ttl_seconds || 900);
    if (!Number.isFinite(ttl) || ttl < 60 || ttl > 86400) {
      return jsonResponse({ error: "ttl_seconds must be between 60 and 86400" }, 400);
    }

    const token = randomToken(20);
    const expiresAt = Date.now() + ttl * 1000;
    await this.setJoinToken(token, {
      token,
      name: body.name.trim(),
      expires_at: expiresAt,
      issued_at: nowIso(),
      used_at: null,
    });

    const joinCommand = `abc join --server ${url.origin} --token ${token}`;
    return jsonResponse({ token, expires_at: new Date(expiresAt).toISOString(), join_command: joinCommand });
  }

  normalizeDevices(devices) {
    const values = Object.values(devices);
    values.sort((a, b) => {
      const ta = Date.parse(a.last_seen_at || 0);
      const tb = Date.parse(b.last_seen_at || 0);
      return tb - ta;
    });
    return values.map((item) => ({
      id: item.id,
      name: item.name,
      last_clipboard: item.last_clipboard || "",
      last_clipboard_at: item.last_clipboard_at || null,
      last_seen_at: item.last_seen_at || null,
      joined_at: item.joined_at || null,
      connected: this.agentSockets.has(item.id),
    }));
  }

  async listDevices(request) {
    if (!(await this.verifyAdmin(request))) {
      return jsonResponse({ error: "Unauthorized" }, 401);
    }
    const devices = await this.getDevicesMap();
    return jsonResponse({ devices: this.normalizeDevices(devices) });
  }

  async joinAgent(request, url) {
    const body = await readJson(request);
    if (!body || typeof body.token !== "string") {
      return jsonResponse({ error: "token is required" }, 400);
    }

    const joinToken = await this.getJoinToken(body.token.trim());
    if (!joinToken) {
      return jsonResponse({ error: "invalid token" }, 404);
    }
    if (joinToken.used_at) {
      return jsonResponse({ error: "token already used" }, 409);
    }
    if (Date.now() > joinToken.expires_at) {
      return jsonResponse({ error: "token expired" }, 410);
    }

    const devices = await this.getDevicesMap();
    const deviceId = `dev_${randomToken(8)}`;
    const deviceSecret = randomToken(24);
    const stamp = nowIso();
    devices[deviceId] = {
      id: deviceId,
      name: joinToken.name,
      secret: deviceSecret,
      joined_at: stamp,
      last_seen_at: stamp,
      last_clipboard: "",
      last_clipboard_at: null,
      pending_clipboard: null,
    };

    joinToken.used_at = stamp;
    await this.state.storage.put(`join:${body.token.trim()}`, joinToken);
    await this.setDevicesMap(devices);
    await this.broadcastDevices();

    return jsonResponse({
      ok: true,
      device_id: deviceId,
      device_secret: deviceSecret,
      name: joinToken.name,
      ws_url: wsUrlFromHttp(url.origin, "/ws/agent", {
        device_id: deviceId,
        device_secret: deviceSecret,
      }),
    });
  }

  async sendToDevice(request, path) {
    if (!(await this.verifyAdmin(request))) {
      return jsonResponse({ error: "Unauthorized" }, 401);
    }
    const body = await readJson(request);
    if (!body || typeof body.text !== "string") {
      return jsonResponse({ error: "text is required" }, 400);
    }

    const parts = path.split("/");
    const deviceId = parts[4];
    const devices = await this.getDevicesMap();
    const device = devices[deviceId];
    if (!device) {
      return jsonResponse({ error: "device not found" }, 404);
    }

    device.pending_clipboard = body.text;
    device.last_seen_at = nowIso();
    devices[deviceId] = device;
    await this.setDevicesMap(devices);

    const socket = this.agentSockets.get(deviceId);
    if (socket) {
      try {
        socket.send(JSON.stringify({ type: "set_clipboard", text: body.text }));
      } catch {
        // Socket may be stale; pending_clipboard remains in storage.
      }
    }
    await this.broadcastDevices();
    return jsonResponse({ ok: true, queued: !socket });
  }

  async acceptAgentSocket(request, url) {
    const upgrade = request.headers.get("Upgrade");
    if (upgrade !== "websocket") {
      return jsonResponse({ error: "Expected websocket" }, 426);
    }

    const deviceId = url.searchParams.get("device_id") || "";
    const deviceSecret = url.searchParams.get("device_secret") || "";
    if (!deviceId || !deviceSecret) {
      return jsonResponse({ error: "device_id and device_secret required" }, 400);
    }

    const devices = await this.getDevicesMap();
    const device = devices[deviceId];
    if (!device || device.secret !== deviceSecret) {
      return jsonResponse({ error: "invalid device credentials" }, 401);
    }

    const pair = new WebSocketPair();
    const [client, server] = Object.values(pair);
    server.serializeAttachment({ role: "agent", deviceId });
    this.state.acceptWebSocket(server);
    this.agentSockets.set(deviceId, server);

    device.last_seen_at = nowIso();
    devices[deviceId] = device;
    await this.setDevicesMap(devices);
    await this.broadcastDevices();

    if (device.pending_clipboard !== null && device.pending_clipboard !== undefined) {
      server.send(JSON.stringify({ type: "set_clipboard", text: device.pending_clipboard }));
    }

    return new Response(null, { status: 101, webSocket: client });
  }

  async acceptDashboardSocket(request, url) {
    const upgrade = request.headers.get("Upgrade");
    if (upgrade !== "websocket") {
      return jsonResponse({ error: "Expected websocket" }, 426);
    }
    if (!(await this.verifyAdmin(request, url))) {
      return jsonResponse({ error: "Unauthorized" }, 401);
    }

    const pair = new WebSocketPair();
    const [client, server] = Object.values(pair);
    server.serializeAttachment({ role: "dashboard" });
    this.state.acceptWebSocket(server);
    this.dashboardSockets.add(server);

    const devices = await this.getDevicesMap();
    server.send(JSON.stringify({ type: "devices", devices: this.normalizeDevices(devices) }));
    return new Response(null, { status: 101, webSocket: client });
  }

  async webSocketMessage(ws, message) {
    const meta = ws.deserializeAttachment();
    if (!meta || meta.role !== "agent") {
      return;
    }

    let payload;
    try {
      payload = JSON.parse(message);
    } catch {
      return;
    }

    const devices = await this.getDevicesMap();
    const device = devices[meta.deviceId];
    if (!device) {
      return;
    }

    if (payload.type === "clipboard" && typeof payload.text === "string") {
      device.last_clipboard = payload.text;
      device.last_clipboard_at = nowIso();
      device.last_seen_at = nowIso();
      if (device.pending_clipboard === payload.text) {
        device.pending_clipboard = null;
      }
      devices[meta.deviceId] = device;
      await this.setDevicesMap(devices);
      await this.broadcastDevices();
      return;
    }

    if (payload.type === "heartbeat") {
      device.last_seen_at = nowIso();
      devices[meta.deviceId] = device;
      await this.setDevicesMap(devices);
      await this.broadcastDevices();
    }
  }

  async webSocketClose(ws) {
    const meta = ws.deserializeAttachment();
    if (!meta) {
      return;
    }
    if (meta.role === "agent" && meta.deviceId) {
      this.agentSockets.delete(meta.deviceId);
      await this.broadcastDevices();
      return;
    }
    if (meta.role === "dashboard") {
      this.dashboardSockets.delete(ws);
    }
  }

  async webSocketError(ws) {
    await this.webSocketClose(ws);
  }

  async broadcastDevices() {
    if (!this.dashboardSockets.size) {
      return;
    }

    const devices = await this.getDevicesMap();
    const msg = JSON.stringify({ type: "devices", devices: this.normalizeDevices(devices) });
    for (const ws of this.dashboardSockets) {
      try {
        ws.send(msg);
      } catch {
        this.dashboardSockets.delete(ws);
      }
    }
  }
}
