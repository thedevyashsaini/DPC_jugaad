const DASHBOARD_HTML = `<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Clipboard Fleet</title>
    <style>
      :root {
        --black: #000;
        --white: #fff;
        --g0: #0a0a0a;
        --g1: #111;
        --g2: #1a1a1a;
        --g3: #1f1f1f;
        --g4: #303030;
      }

      * { box-sizing: border-box; }
      html, body { height: 100%; }

      body {
        margin: 0;
        background: var(--black);
        color: var(--white);
        font-family: "SF Pro Text", "Helvetica Neue", "Inter", "Segoe UI", sans-serif;
        font-weight: 400;
      }

      .app {
        width: 100vw;
        height: 100vh;
        border: 1px solid #1b1b1b;
        background: var(--black);
      }

      .top {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 12px;
        padding: 14px 16px;
        border-bottom: 1px solid #1b1b1b;
      }

      .branding {
        display: flex;
        align-items: center;
        gap: 10px;
      }

      .mark {
        width: 36px;
        height: 36px;
        border: 1px solid #3a3a3a;
        background: var(--g1);
      }

      .title {
        margin: 0;
        font-size: clamp(22px, 2.3vw, 36px);
        font-weight: 580;
        letter-spacing: -0.015em;
        line-height: 1;
      }

      .sub {
        margin: 4px 0 0;
        color: #9b9b9b;
        font-size: 12px;
      }

      .badge {
        border: 1px solid #3a3a3a;
        padding: 4px 9px;
        font-size: 11px;
        font-weight: 600;
        color: var(--white);
        background: var(--g1);
      }

      .layout {
        display: grid;
        grid-template-columns: 360px 1fr;
        height: calc(100% - 80px);
      }

      .sidebar {
        border-right: 1px solid #1b1b1b;
        overflow: auto;
      }

      .main {
        overflow: auto;
      }

      .stack {
        display: grid;
        gap: 0;
      }

      .card,
      .panel {
        border-bottom: 1px solid #1b1b1b;
        padding: 9px;
        background: var(--black);
      }

      .eyebrow {
        margin: 0 0 7px;
        text-transform: uppercase;
        letter-spacing: 0.11em;
        font-size: 10px;
        color: #b2b2b2;
        font-weight: 600;
      }

      .row {
        display: flex;
        gap: 8px;
        align-items: center;
        flex-wrap: wrap;
      }

      input,
      textarea {
        width: 100%;
        border: 1px solid #252525;
        background: var(--g0);
        color: var(--white);
        font: inherit;
        font-size: 15px;
        padding: 8px 9px;
      }

      input:focus,
      textarea:focus {
        outline: none;
        border-color: #5f5f5f;
      }

      textarea {
        min-height: 230px;
        resize: vertical;
      }

      button {
        border: 1px solid #2f2f2f;
        background: var(--g1);
        color: var(--white);
        padding: 7px 11px;
        font: inherit;
        font-size: 15px;
        font-weight: 560;
        cursor: pointer;
      }

      button:hover {
        background: var(--g2);
      }

      button.primary {
        border-color: #5f5f5f;
      }

      button.ghost {
        border-color: var(--g4);
      }

      .meta {
        font-size: 12px;
        color: #a5a5a5;
      }

      .status,
      .status.ok,
      .status.err {
        font-size: 13px;
        color: var(--white);
      }

      .device-list {
        max-height: 46vh;
        min-height: 220px;
        overflow: auto;
      }

      .device {
        width: 100%;
        text-align: left;
        border: 1px solid #1f1f1f;
        padding: 9px;
        background: var(--g0);
        color: var(--white);
        cursor: pointer;
        margin-bottom: 8px;
      }

      .device:hover {
        border-color: #4b4b4b;
      }

      .device.active {
        border-color: #595959;
        background: var(--g1);
      }

      .dot {
        display: inline-block;
        width: 8px;
        height: 8px;
        border-radius: 0;
        margin-right: 6px;
        background: var(--white);
      }

      .dot.live {
        background: var(--white);
      }

      .split {
        display: grid;
        grid-template-columns: 1.25fr 1fr;
        gap: 0;
        border-top: 1px solid var(--g3);
      }

      .split .panel {
        border-bottom: 0;
      }

      .split .panel + .panel {
        border-left: 1px solid var(--g3);
      }

      .clip-view {
        min-height: 186px;
        border: 1px solid var(--g3);
        padding: 12px;
        white-space: pre-wrap;
        word-break: break-word;
        background: var(--g0);
      }

      pre {
        margin: 0;
        border: 1px solid var(--g3);
        background: var(--g0);
        color: var(--white);
        padding: 10px;
        overflow: auto;
      }

      .history {
        max-height: 320px;
        min-height: 220px;
        overflow: auto;
      }

      .hist-item {
        border: 1px solid var(--g3);
        background: var(--g0);
        padding: 9px;
        margin-bottom: 8px;
      }

      .hist-text {
        font-size: 13px;
        white-space: pre-wrap;
        word-break: break-word;
      }

      .hist-time {
        margin-top: 6px;
        font-size: 11px;
        color: #bdbdbd;
      }

      @media (max-width: 1180px) {
        .layout {
          grid-template-columns: 1fr;
          height: auto;
        }

        .sidebar {
          border-right: 0;
          border-bottom: 1px solid var(--g3);
        }

        .split {
          grid-template-columns: 1fr;
        }

        .split .panel + .panel {
          border-left: 0;
          border-top: 1px solid var(--g3);
        }

        .device-list {
          max-height: 36vh;
        }
      }
    </style>
  </head>
  <body>
    <main class="app">
      <header class="top">
        <div>
          <div class="branding">
            <div class="mark"></div>
            <div>
              <h1 class="title">Clipboard Fleet</h1>
            </div>
          </div>
          <p class="sub">Live clipboard console for all joined machines</p>
        </div>
        <div class="badge offline" id="badge">Disconnected</div>
      </header>

      <section class="layout">
        <aside class="sidebar">
          <div class="stack">
            <div class="card soft">
              <p class="eyebrow">Admin Access</p>
              <input id="adminToken" placeholder="Admin token" />
              <div class="row" style="margin-top:8px;">
                <button class="primary" id="connectBtn">Connect</button>
                <button class="ghost" id="refreshBtn">Refresh</button>
              </div>
            </div>

            <div class="card soft">
              <p class="eyebrow">Create Join Command</p>
              <input id="nameInput" placeholder="Device name (eg. dev-laptop)" />
              <div style="height:8px;"></div>
              <input id="ttlInput" type="number" value="900" min="0" />
              <div class="meta" style="margin-top:6px;">TTL seconds (0 = never expires)</div>
              <div class="row" style="margin-top:10px;">
                <button class="primary" id="createTokenBtn">Generate Token</button>
              </div>
              <div style="height:10px;"></div>
              <pre id="joinCommand">No token generated yet</pre>
            </div>

            <div class="card soft">
              <p class="eyebrow">Danger Zone</p>
              <div class="row">
                <button class="ghost" id="nukeTokensBtn">Nuke Tokens</button>
                <button class="ghost" id="nukeDevicesBtn">Nuke Devices</button>
              </div>
            </div>

            <div class="card">
              <p class="eyebrow">Joined Devices</p>
              <div class="device-list" id="deviceList"></div>
            </div>
          </div>
        </aside>

        <section class="main">
          <div class="stack">
            <div class="panel">
              <p class="eyebrow">Selected Device Clipboard</p>
              <div class="clip-view" id="clipboardView">Select a device to inspect clipboard</div>
            </div>

            <div class="split">
              <div class="panel">
                <p class="eyebrow">Send To Selected Device</p>
                <textarea id="sendInput" placeholder="Type text and push it directly to selected machine clipboard"></textarea>
                <div class="row" style="margin-top:10px;">
                  <button class="primary" id="sendBtn">Send Clipboard</button>
                  <span class="status" id="status">Ready</span>
                </div>
              </div>

              <div class="panel">
                <p class="eyebrow">Clipboard History</p>
                <div class="history" id="clipHistory"></div>
              </div>
            </div>
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
      const clipHistory = document.getElementById("clipHistory");
      const sendInput = document.getElementById("sendInput");
      const sendBtn = document.getElementById("sendBtn");
      const statusEl = document.getElementById("status");
      const badge = document.getElementById("badge");
      const nukeTokensBtn = document.getElementById("nukeTokensBtn");
      const nukeDevicesBtn = document.getElementById("nukeDevicesBtn");

      let selectedDeviceId = null;
      let devices = [];
      let stream = null;

      const cachedToken = localStorage.getItem("clipboard_admin_token") || "";
      if (cachedToken) {
        adminTokenInput.value = cachedToken;
      }

      function setStatus(text, type) {
        statusEl.textContent = text;
        statusEl.className = "status " + (type || "");
      }

      function setBadgeState(text, mode) {
        badge.textContent = text;
        badge.className = "badge " + (mode || "offline");
      }

      function shortClip(text, limit) {
        const value = text || "";
        if (value.length <= limit) return value;
        return value.slice(0, limit) + "...";
      }

      function escapeHtml(value) {
        return (value || "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
      }

      function showDevices() {
        deviceList.innerHTML = "";
        if (!devices.length) {
          deviceList.innerHTML = '<div class="meta">No joined devices yet</div>';
          clipboardView.textContent = "No joined devices";
          clipHistory.innerHTML = '<div class="meta">No clipboard history yet</div>';
          return;
        }

        const exists = devices.some((x) => x.id === selectedDeviceId);
        if (!exists) {
          selectedDeviceId = devices[0].id;
        }

        for (const device of devices) {
          const btn = document.createElement("button");
          const liveClass = device.connected ? "live" : "";
          btn.className = "device " + (device.id === selectedDeviceId ? "active" : "");
          btn.type = "button";
          btn.innerHTML =
            '<div><strong>' +
            escapeHtml(device.name) +
            '</strong></div>' +
            '<div class="meta"><span class="dot ' +
            liveClass +
            '"></span>' +
            (device.connected ? "Online" : "Offline") +
            ' - Last seen ' +
            new Date(device.last_seen_at || 0).toLocaleString() +
            "</div>" +
            '<div class="meta">' +
            escapeHtml(shortClip(device.last_clipboard || "", 76)) +
            "</div>";

          btn.addEventListener("click", () => {
            selectedDeviceId = device.id;
            showDevices();
          });
          deviceList.appendChild(btn);
        }

        const selected = devices.find((d) => d.id === selectedDeviceId);
        clipboardView.textContent = selected ? selected.last_clipboard || "(empty clipboard)" : "Select a device";
        renderHistory(selected ? selected.clipboard_history || [] : []);
      }

      function renderHistory(items) {
        clipHistory.innerHTML = "";
        if (!items.length) {
          clipHistory.innerHTML = '<div class="meta">No clipboard history yet</div>';
          return;
        }
        for (const item of items) {
          const row = document.createElement("div");
          row.className = "hist-item";
          row.innerHTML =
            '<div class="hist-text">' + escapeHtml(item.text || "") + "</div>" +
            '<div class="hist-time">' + new Date(item.at || 0).toLocaleString() + "</div>";
          clipHistory.appendChild(row);
        }
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

      async function nuke(kind) {
        try {
          const body = {
            tokens: kind === "tokens" || kind === "both",
            devices: kind === "devices" || kind === "both"
          };
          const res = await authedFetch("/api/admin/nuke", {
            method: "POST",
            headers: { "content-type": "application/json" },
            body: JSON.stringify(body),
          });
          if (!res.ok) throw new Error("HTTP " + res.status);
          const data = await res.json();
          setStatus("Nuke complete: tokens=" + data.deleted_tokens + " devices=" + data.deleted_devices, "ok");
          await refreshDevices();
        } catch (err) {
          setStatus(err.message || "Nuke failed", "err");
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
          setBadgeState("Live", "live");
          setStatus("Live updates connected", "ok");
        };
        stream.onerror = () => {
          setBadgeState("Reconnecting", "offline");
          setStatus("Live stream reconnecting", "err");
        };
        stream.onclose = () => {
          setBadgeState("Disconnected", "offline");
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
      nukeTokensBtn.addEventListener("click", () => nuke("tokens"));
      nukeDevicesBtn.addEventListener("click", () => nuke("devices"));

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

const MAX_PENDING_COMMANDS = 200;
const MAX_RECENT_EVENT_IDS = 500;
const ONLINE_STALE_MS = 18000;

function commandId() {
  return `cmd_${randomToken(10)}`;
}

function ensureDeviceQueues(device) {
  if (!Array.isArray(device.pending_commands)) {
    device.pending_commands = [];
  }
  if (!Array.isArray(device.recent_clipboard_event_ids)) {
    device.recent_clipboard_event_ids = [];
  }
}

function hasRecentEventId(device, eventId) {
  ensureDeviceQueues(device);
  return device.recent_clipboard_event_ids.includes(eventId);
}

function addRecentEventId(device, eventId) {
  ensureDeviceQueues(device);
  if (device.recent_clipboard_event_ids.includes(eventId)) {
    return;
  }
  device.recent_clipboard_event_ids.push(eventId);
  if (device.recent_clipboard_event_ids.length > MAX_RECENT_EVENT_IDS) {
    device.recent_clipboard_event_ids = device.recent_clipboard_event_ids.slice(
      device.recent_clipboard_event_ids.length - MAX_RECENT_EVENT_IDS
    );
  }
}

function removePendingCommand(device, cmdId) {
  ensureDeviceQueues(device);
  const before = device.pending_commands.length;
  device.pending_commands = device.pending_commands.filter((x) => x.cmd_id !== cmdId);
  return before !== device.pending_commands.length;
}

function appendClipboardHistory(device, text) {
  if (!Array.isArray(device.clipboard_history)) {
    device.clipboard_history = [];
  }
  const head = device.clipboard_history[0];
  if (head && head.text === text) {
    return;
  }
  device.clipboard_history.unshift({ text, at: nowIso() });
  if (device.clipboard_history.length > 100) {
    device.clipboard_history = device.clipboard_history.slice(0, 100);
  }
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
    if (path === "/api/admin/nuke" && request.method === "POST") {
      return this.nukeState(request);
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

  sendPendingCommandsToSocket(socket, device) {
    ensureDeviceQueues(device);
    for (const cmd of device.pending_commands) {
      try {
        socket.send(
          JSON.stringify({
            type: "set_clipboard",
            cmd_id: cmd.cmd_id,
            text: cmd.text,
            created_at: cmd.created_at,
          })
        );
      } catch {
        break;
      }
    }
  }

  pruneStaleAgentSockets(devices) {
    const now = Date.now();
    for (const [deviceId, ws] of this.agentSockets.entries()) {
      const device = devices[deviceId];
      const lastSeen = device && device.last_seen_at ? Date.parse(device.last_seen_at) : 0;
      if (!lastSeen || now - lastSeen > ONLINE_STALE_MS) {
        this.agentSockets.delete(deviceId);
        try {
          ws.close(1012, "stale connection");
        } catch {}
      }
    }
  }

  async createJoinToken(request, url) {
    if (!(await this.verifyAdmin(request))) {
      return jsonResponse({ error: "Unauthorized" }, 401);
    }

    const body = await readJson(request);
    if (!body || typeof body.name !== "string" || !body.name.trim()) {
      return jsonResponse({ error: "name is required" }, 400);
    }

    const ttl = Number(body.ttl_seconds ?? 900);
    if (!Number.isFinite(ttl) || ttl < 0 || ttl > 315360000) {
      return jsonResponse({ error: "ttl_seconds must be between 0 and 315360000" }, 400);
    }

    const token = randomToken(20);
    const expiresAt = ttl === 0 ? null : Date.now() + ttl * 1000;
    await this.setJoinToken(token, {
      token,
      name: body.name.trim(),
      expires_at: expiresAt,
      issued_at: nowIso(),
      used_at: null,
    });

    const joinCommand = `abc join --server ${url.origin} --token ${token}`;
    return jsonResponse({
      token,
      expires_at: expiresAt ? new Date(expiresAt).toISOString() : null,
      never_expires: expiresAt === null,
      join_command: joinCommand,
    });
  }

  normalizeDevices(devices) {
    const values = Object.values(devices);
    const now = Date.now();
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
      connected: item.last_seen_at && now - Date.parse(item.last_seen_at) <= ONLINE_STALE_MS,
      clipboard_history: Array.isArray(item.clipboard_history) ? item.clipboard_history : [],
      pending_count: Array.isArray(item.pending_commands) ? item.pending_commands.length : 0,
    }));
  }

  async nukeState(request) {
    if (!(await this.verifyAdmin(request))) {
      return jsonResponse({ error: "Unauthorized" }, 401);
    }
    const body = (await readJson(request)) || {};
    const wipeTokens = !!body.tokens;
    const wipeDevices = !!body.devices;

    let deletedTokens = 0;
    let deletedDevices = 0;

    if (wipeTokens) {
      const entries = await this.state.storage.list({ prefix: "join:" });
      const keys = [];
      for (const key of entries.keys()) {
        keys.push(key);
      }
      if (keys.length) {
        await this.state.storage.delete(keys);
      }
      deletedTokens = keys.length;
    }

    if (wipeDevices) {
      const devices = await this.getDevicesMap();
      deletedDevices = Object.keys(devices).length;
      await this.setDevicesMap({});
      for (const ws of this.agentSockets.values()) {
        try {
          ws.close(1012, "Devices wiped by admin");
        } catch {}
      }
      this.agentSockets.clear();
    }

    await this.broadcastDevices();
    return jsonResponse({ ok: true, deleted_tokens: deletedTokens, deleted_devices: deletedDevices });
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
    if (joinToken.expires_at !== null && Date.now() > joinToken.expires_at) {
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
      pending_commands: [],
      recent_clipboard_event_ids: [],
      clipboard_history: [],
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

    ensureDeviceQueues(device);
    const cmd = {
      cmd_id: commandId(),
      text: body.text,
      created_at: nowIso(),
    };
    device.pending_commands.push(cmd);
    if (device.pending_commands.length > MAX_PENDING_COMMANDS) {
      device.pending_commands = device.pending_commands.slice(
        device.pending_commands.length - MAX_PENDING_COMMANDS
      );
    }
    appendClipboardHistory(device, body.text);
    devices[deviceId] = device;
    await this.setDevicesMap(devices);

    const socket = this.agentSockets.get(deviceId);
    if (socket) {
      try {
        this.sendPendingCommandsToSocket(socket, device);
      } catch {
        this.agentSockets.delete(deviceId);
      }
    }
    await this.broadcastDevices();
    return jsonResponse({ ok: true, queued: !socket, cmd_id: cmd.cmd_id });
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
    ensureDeviceQueues(device);
    devices[deviceId] = device;
    await this.setDevicesMap(devices);
    await this.broadcastDevices();

    this.sendPendingCommandsToSocket(server, device);

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
      const eventId = typeof payload.event_id === "string" ? payload.event_id : null;
      if (eventId && hasRecentEventId(device, eventId)) {
        try {
          ws.send(JSON.stringify({ type: "ack_clipboard", event_id: eventId }));
        } catch {}
        return;
      }

      if (eventId) {
        addRecentEventId(device, eventId);
      }
      device.last_seen_at = nowIso();

      if (payload.text !== "out") {
        device.last_clipboard = payload.text;
        device.last_clipboard_at = nowIso();
        appendClipboardHistory(device, payload.text);
      }

      devices[meta.deviceId] = device;
      await this.setDevicesMap(devices);
      await this.broadcastDevices();

      if (eventId) {
        try {
          ws.send(JSON.stringify({ type: "ack_clipboard", event_id: eventId }));
        } catch {}
      }
      return;
    }

    if (payload.type === "ack_command" && typeof payload.cmd_id === "string") {
      ensureDeviceQueues(device);
      const changed = removePendingCommand(device, payload.cmd_id);
      if (changed) {
        device.last_seen_at = nowIso();
        devices[meta.deviceId] = device;
        await this.setDevicesMap(devices);
        await this.broadcastDevices();
      }
      return;
    }

    if (payload.type === "heartbeat") {
      device.last_seen_at = nowIso();
      devices[meta.deviceId] = device;
      await this.setDevicesMap(devices);
      this.sendPendingCommandsToSocket(ws, device);
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
    this.pruneStaleAgentSockets(devices);
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
