from __future__ import annotations

import asyncio
import json
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pyperclip
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel


HISTORY_FILE = Path(__file__).with_name("clipboard_history.json")
MAX_HISTORY = 250
UI_VERSION = "sse-v2"


HTML = """<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Clipboard Deck</title>
    <style>
  :root {
    --bg: #000;
    --border-subtle: #222;
    --border-stark: #fff;
    --text: #fff;
    --muted: #888;
  }

  /* * Strict geometric rules: 
   * Absolute rectangles, zero curves. 
   */
  * {
    box-sizing: border-box;
    border-radius: 0 !important; 
  }

  html, body {
    margin: 0;
    background: var(--bg);
    color: var(--text);
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    -webkit-font-smoothing: antialiased;
  }

  body {
    padding: 32px 16px;
  }

  .app {
    max-width: 1100px;
    margin: 0 auto;
    /* Removed the outer bounding box */
  }

  /* HEADER */
  .top {
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
    padding-bottom: 32px;
    margin-bottom: 48px;
    border-bottom: 1px solid var(--border-stark);
  }

  .title {
    margin: 0;
    font-size: 28px;
    font-weight: 700;
    letter-spacing: -0.03em;
  }

  .sub {
    margin: 8px 0 0;
    font-size: 14px;
    color: var(--muted);
  }

  .badge {
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: var(--text);
    border: 1px solid var(--border-subtle);
    padding: 6px 10px;
  }

  /* LAYOUT */
  .grid {
    display: grid;
    grid-template-columns: 320px 1fr;
    gap: 64px; /* Using negative space instead of borders */
    min-height: 70vh;
  }

  .panel {
    padding: 0;
  }

  .panel-head {
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid var(--border-subtle);
    padding-bottom: 16px;
    margin-bottom: 24px;
  }

  .eyebrow {
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: var(--text);
    margin: 0;
  }

  /* HISTORY LIST */
  .history {
    display: flex;
    flex-direction: column;
  }

  .item {
    padding: 16px 0;
    border: none;
    border-bottom: 1px solid var(--border-subtle);
    background: transparent;
    text-align: left;
    cursor: pointer;
    transition: padding-left 0.2s ease, border-color 0.2s ease;
  }

  .item:hover {
    padding-left: 12px;
    border-bottom-color: var(--text);
  }

  .item.active {
    border-bottom-color: var(--text);
  }

  .item.active .item-text::before {
    content: '■ ';
    font-size: 10px;
    vertical-align: middle;
    margin-right: 4px;
  }

  .item-text {
    font-size: 14px;
    line-height: 1.5;
    color: var(--text);
  }

  .item-time {
    font-size: 11px;
    color: var(--muted);
    margin-top: 8px;
  }

  .empty {
    color: var(--muted);
    font-size: 13px;
    text-align: left;
    margin-top: 16px;
  }

  /* RIGHT SIDE / COMPOSE */
  .compose {
    display: flex;
    flex-direction: column;
    gap: 24px;
  }

  .live {
    border: 1px solid var(--border-subtle);
    background: transparent;
    padding: 20px;
    font-size: 14px;
    line-height: 1.6;
    min-height: 140px;
    font-family: 'JetBrains Mono', 'Fira Code', monospace;
    color: var(--muted);
  }

  textarea {
    width: 100%;
    min-height: 200px;
    background: transparent;
    border: none;
    border-bottom: 1px solid var(--border-subtle);
    color: var(--text);
    padding: 16px 0;
    font-size: 15px;
    line-height: 1.6;
    font-family: inherit;
    resize: vertical;
    transition: border-color 0.2s ease;
  }

  textarea::placeholder {
    color: #444;
  }

  textarea:focus {
    outline: none;
    border-bottom-color: var(--border-stark);
  }

  /* BUTTONS & ACTIONS */
  .actions {
    display: flex;
    gap: 12px;
    align-items: center;
    margin-top: 8px;
  }

  .btn, .ghost {
    font-family: inherit;
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    padding: 12px 24px;
    cursor: pointer;
    transition: all 0.2s ease;
  }

  /* Primary Action */
  .btn {
    background: var(--text);
    color: var(--bg);
    border: 1px solid var(--text);
  }

  .btn:hover {
    background: var(--bg);
    color: var(--text);
  }

  .btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  /* Secondary Action */
  .ghost {
    background: transparent;
    color: var(--text);
    border: 1px solid var(--border-subtle);
  }

  .ghost:hover {
    border-color: var(--text);
  }

  .status {
    font-size: 12px;
    color: var(--muted);
    margin-left: auto; /* Pushes status to the far right */
  }

  .status.ok {
    color: var(--text);
  }

  .status.err {
    color: #ff3333; /* The only color exception, necessary for strict error UX */
  }

  /* RESPONSIVE */
  @media (max-width: 900px) {
    .grid {
      grid-template-columns: 1fr;
      gap: 48px;
    }
    .top {
      flex-direction: column;
      align-items: flex-start;
      gap: 16px;
    }
  }
</style>
  </head>
  <body>
    <div class="grain"></div>
    <main class="app">
      <header class="top">
        <div>
          <h1 class="title">Clipboard Deck</h1>
          <p class="sub">Copy anywhere on host machine, pull from any device on LAN.</p>
        </div>
        <div class="badge" id="hostBadge">LAN</div>
      </header>

      <section class="grid">
        <aside class="left panel">
          <div class="panel-head">
            <p class="eyebrow">Clipboard History</p>
            <button class="ghost" id="clearBtn" type="button">Clear</button>
          </div>
          <div class="history" id="historyList"></div>
        </aside>

        <section class="right panel">
          <div class="compose">
            <p class="eyebrow">Current Host Clipboard</p>
            <div class="live" id="liveClipboard">Loading...</div>
            <p class="eyebrow">Push Text To Host Clipboard</p>
            <textarea
              id="clipboardInput"
              placeholder="Write text here. Press send, then paste anywhere on host."
            ></textarea>
            <div class="actions">
              <button class="btn" id="sendBtn" type="button">Send To Clipboard</button>
              <button class="ghost" id="refreshBtn" type="button">Refresh</button>
              <span class="status" id="statusLine">Ready</span>
            </div>
          </div>
        </section>
      </section>
    </main>

    <script>
      const hostBadge = document.getElementById("hostBadge");
      const historyList = document.getElementById("historyList");
      const liveClipboard = document.getElementById("liveClipboard");
      const input = document.getElementById("clipboardInput");
      const statusLine = document.getElementById("statusLine");
      const sendBtn = document.getElementById("sendBtn");
      const refreshBtn = document.getElementById("refreshBtn");
      const clearBtn = document.getElementById("clearBtn");

      hostBadge.textContent = `LAN Mode - ${location.host} - sse-v2`;

      let activeId = null;
      let latestText = null;

      function shortText(value) {
        const text = value || "(empty clipboard)";
        return text.length > 400 ? `${text.slice(0, 400)}...` : text;
      }

      function friendlyTime(ts) {
        try {
          return new Date(ts).toLocaleString();
        } catch {
          return "just now";
        }
      }

      function setStatus(text, type) {
        statusLine.className = "status";
        if (type) {
          statusLine.classList.add(type);
        }
        statusLine.textContent = text;
      }

      function renderHistory(items) {
        historyList.innerHTML = "";

        if (!items.length) {
          const empty = document.createElement("div");
          empty.className = "empty";
          empty.textContent = "No clips yet. Copy something on your host machine.";
          historyList.appendChild(empty);
          return;
        }

        for (const item of items) {
          const row = document.createElement("button");
          row.type = "button";
          row.className = "item";
          if (item.id === activeId) {
            row.classList.add("active");
          }

          row.innerHTML = `
            <div class="item-text">${shortText(item.text).replace(/</g, "&lt;")}</div>
            <div class="item-time">${friendlyTime(item.created_at)}</div>
          `;

          row.addEventListener("click", async () => {
            activeId = item.id;
            input.value = item.text;
            await sendClipboard(item.text, false);
            await refreshAll();
          });

          historyList.appendChild(row);
        }
      }

      async function refreshAll() {
        try {
          const state = await loadState();

          if (state.text !== latestText) {
            liveClipboard.textContent = state.text || "(clipboard is empty)";
            latestText = state.text;
          }

          if (!activeId && state.history.length) {
            activeId = state.history[0].id;
          }

          renderHistory(state.history);
          setStatus(`Updated ${friendlyTime(state.updated_at)}`, "ok");
        } catch (err) {
          setStatus("Server unreachable", "err");
        }
      }

      async function sendClipboard(value, fromInput = true) {
        try {
          sendBtn.disabled = true;
          setStatus("Sending to host clipboard...", null);

          const payload = { text: fromInput ? input.value : value };

          const res = await fetch("/clipboard", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
          });

          if (!res.ok) {
            throw new Error(`send HTTP ${res.status}`);
          }

          setStatus("Copied to host clipboard", "ok");
        } catch (err) {
          setStatus("Clipboard send failed", "err");
        } finally {
          sendBtn.disabled = false;
        }
      }

      sendBtn.addEventListener("click", async () => {
        await sendClipboard(input.value, false);
        await refreshAll();
      });

      refreshBtn.addEventListener("click", refreshAll);

      clearBtn.addEventListener("click", async () => {
        try {
          const res = await fetch("/history", { method: "DELETE" });
          if (!res.ok) {
            throw new Error(`clear HTTP ${res.status}`);
          }
          activeId = null;
          await refreshAll();
        } catch {
          setStatus("Unable to clear history", "err");
        }
      });

      function applyState(state) {
        if (state.text !== latestText) {
          liveClipboard.textContent = state.text || "(clipboard is empty)";
          latestText = state.text;
        }

        if (!activeId && state.history.length) {
          activeId = state.history[0].id;
        }

        renderHistory(state.history);
        setStatus(`Updated ${friendlyTime(state.updated_at)}`, "ok");
      }

      async function loadState() {
        const res = await fetch("/state", { cache: "no-store" });
        if (!res.ok) {
          throw new Error(`state HTTP ${res.status}`);
        }
        return res.json();
      }

      function connectEvents() {
        const stream = new EventSource("/events");

        stream.onmessage = (event) => {
          try {
            const state = JSON.parse(event.data);
            applyState(state);
          } catch {
            setStatus("Bad event payload", "err");
          }
        };

        stream.onerror = () => {
          setStatus("Live stream disconnected, retrying...", "err");
        };
      }

      refreshAll();
      connectEvents();
    </script>
  </body>
</html>
"""


class ClipboardPayload(BaseModel):
    text: str


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def clip_id() -> str:
    now = datetime.now(timezone.utc)
    return now.strftime("%Y%m%d%H%M%S%f")


def load_history_from_disk() -> list[dict[str, str]]:
    if not HISTORY_FILE.exists():
        return []

    try:
        data = json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []

    if not isinstance(data, list):
        return []

    cleaned: list[dict[str, str]] = []
    for item in data:
        if isinstance(item, dict):
            text = item.get("text")
            created = item.get("created_at")
            item_id = item.get("id")
            if (
                isinstance(text, str)
                and isinstance(created, str)
                and isinstance(item_id, str)
            ):
                cleaned.append({"id": item_id, "text": text, "created_at": created})
    return cleaned[:MAX_HISTORY]


def save_history_to_disk(history: list[dict[str, str]]) -> None:
    HISTORY_FILE.write_text(
        json.dumps(history[:MAX_HISTORY], ensure_ascii=True, indent=2),
        encoding="utf-8",
    )


def push_history(state: Any, text: str, stamp: str) -> None:
    if state.history and state.history[0]["text"] == text:
        return

    item = {"id": clip_id(), "text": text, "created_at": stamp}
    state.history.insert(0, item)
    state.history = state.history[:MAX_HISTORY]
    save_history_to_disk(state.history)


async def publish_change(state: Any) -> None:
    async with state.condition:
        state.version += 1
        state.condition.notify_all()


def build_state_payload(state: Any) -> dict[str, Any]:
    return {
        "text": state.clipboard_text,
        "updated_at": state.updated_at,
        "history": [dict(item) for item in state.history],
        "version": state.version,
    }


@asynccontextmanager
async def lifespan(app: FastAPI):
    state = app.state
    state.clipboard_text = ""
    state.updated_at = utc_timestamp()
    state.history = load_history_from_disk()
    state.lock = asyncio.Lock()
    state.condition = asyncio.Condition()
    state.version = 0
    state.stop_event = asyncio.Event()
    state.poll_seconds = 0.25

    try:
        initial = pyperclip.paste()
        if isinstance(initial, str):
            state.clipboard_text = initial
            push_history(state, initial, state.updated_at)
    except pyperclip.PyperclipException:
        pass

    async def watcher() -> None:
        while not state.stop_event.is_set():
            try:
                now = pyperclip.paste()
                if not isinstance(now, str):
                    now = str(now)
            except pyperclip.PyperclipException:
                await asyncio.sleep(state.poll_seconds)
                continue

            changed = False
            async with state.lock:
                if now != state.clipboard_text:
                    stamp = utc_timestamp()
                    state.clipboard_text = now
                    state.updated_at = stamp
                    push_history(state, now, stamp)
                    changed = True

            if changed:
                await publish_change(state)

            await asyncio.sleep(state.poll_seconds)

    watcher_task = asyncio.create_task(watcher(), name="clipboard-watcher")
    try:
        yield
    finally:
        state.stop_event.set()
        watcher_task.cancel()
        try:
            await watcher_task
        except asyncio.CancelledError:
            pass


app = FastAPI(title="Clipboard Bridge", lifespan=lifespan)


@app.get("/", response_class=HTMLResponse)
async def home() -> str:
    return HTMLResponse(
        content=HTML,
        headers={
            "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
            "Pragma": "no-cache",
            "Expires": "0",
        },
    )


@app.get("/state")
async def get_state() -> dict[str, Any]:
    async with app.state.lock:
        return build_state_payload(app.state)


@app.get("/events")
async def events(request: Request) -> StreamingResponse:
    async def event_stream():
        last_version = -1
        while True:
            if await request.is_disconnected():
                break

            async with app.state.lock:
                payload = build_state_payload(app.state)

            if payload["version"] != last_version:
                last_version = payload["version"]
                data = json.dumps(payload, ensure_ascii=True)
                yield f"data: {data}\n\n"
                continue

            async with app.state.condition:
                try:
                    await asyncio.wait_for(app.state.condition.wait(), timeout=25)
                except asyncio.TimeoutError:
                    yield ": keep-alive\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )


@app.get("/clipboard")
async def get_clipboard() -> dict[str, Any]:
    async with app.state.lock:
        return {
            "text": app.state.clipboard_text,
            "updated_at": app.state.updated_at,
        }


@app.post("/clipboard")
async def set_clipboard(payload: ClipboardPayload) -> dict[str, Any]:
    text = payload.text
    if not isinstance(text, str):
        raise HTTPException(status_code=400, detail="Text payload is required")

    try:
        pyperclip.copy(text)
    except pyperclip.PyperclipException as exc:
        raise HTTPException(
            status_code=500, detail=f"Clipboard write failed: {exc}"
        ) from exc

    async with app.state.lock:
        stamp = utc_timestamp()
        app.state.clipboard_text = text
        app.state.updated_at = stamp
        push_history(app.state, text, stamp)

    await publish_change(app.state)

    return {"ok": True, "updated_at": app.state.updated_at}


@app.get("/history")
async def get_history() -> dict[str, Any]:
    async with app.state.lock:
        return {"items": app.state.history}


@app.delete("/history")
async def clear_history() -> dict[str, bool]:
    async with app.state.lock:
        app.state.history = []
        save_history_to_disk(app.state.history)

    await publish_change(app.state)
    return {"ok": True}
