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
        --bg: #f3efe7;
        --ink: #1f1d1a;
        --muted: #6b6459;
        --line: #dfd7c9;
        --panel: rgba(255, 255, 255, 0.72);
        --panel-strong: rgba(255, 255, 255, 0.92);
        --brand: #ff5a36;
        --brand-2: #ffc23c;
        --ok: #1f9854;
        --err: #c92a2a;
        --shadow: 0 30px 80px rgba(21, 16, 5, 0.12);
      }

      * {
        box-sizing: border-box;
      }

      html,
      body {
        margin: 0;
        min-height: 100%;
        font-family: "Plus Jakarta Sans", "Avenir Next", "Segoe UI", sans-serif;
        color: var(--ink);
        background:
          radial-gradient(900px 460px at 100% -20%, rgba(255, 90, 54, 0.18), transparent 70%),
          radial-gradient(700px 340px at 0% 0%, rgba(255, 194, 60, 0.24), transparent 70%),
          var(--bg);
      }

      body {
        padding: clamp(12px, 2vw, 24px);
      }

      .grain {
        position: fixed;
        inset: 0;
        pointer-events: none;
        opacity: 0.22;
        background-image: radial-gradient(rgba(0, 0, 0, 0.12) 0.5px, transparent 0.5px);
        background-size: 3px 3px;
      }

      .app {
        position: relative;
        z-index: 2;
        width: min(1300px, 100%);
        margin: 0 auto;
        border: 1px solid var(--line);
        background: linear-gradient(150deg, var(--panel), rgba(255, 255, 255, 0.65));
        backdrop-filter: blur(8px);
        border-radius: 24px;
        box-shadow: var(--shadow);
        overflow: hidden;
      }

      .top {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 16px;
        padding: 18px 20px;
        border-bottom: 1px solid var(--line);
        background: linear-gradient(180deg, rgba(255, 255, 255, 0.86), rgba(255, 255, 255, 0.48));
      }

      .title {
        margin: 0;
        line-height: 1;
        font-size: clamp(22px, 3vw, 34px);
        letter-spacing: -0.02em;
      }

      .sub {
        margin: 4px 0 0;
        color: var(--muted);
        font-size: 14px;
      }

      .badge {
        border-radius: 999px;
        border: 1px solid #ffd5cb;
        background: linear-gradient(135deg, #ffe5de, #fff4d5);
        color: #6f2e1f;
        padding: 8px 12px;
        font-size: 12px;
        font-weight: 700;
        white-space: nowrap;
      }

      .grid {
        display: grid;
        grid-template-columns: minmax(280px, 420px) 1fr;
        min-height: calc(100vh - 120px);
      }

      .left {
        border-right: 1px solid var(--line);
        background: linear-gradient(180deg, rgba(255, 255, 255, 0.72), rgba(255, 255, 255, 0.38));
      }

      .right {
        background: linear-gradient(180deg, rgba(255, 255, 255, 0.42), rgba(255, 255, 255, 0.14));
      }

      .panel {
        padding: 18px;
      }

      .panel-head {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 12px;
        gap: 8px;
      }

      .eyebrow {
        margin: 0;
        text-transform: uppercase;
        letter-spacing: 0.09em;
        font-size: 11px;
        color: var(--muted);
        font-weight: 700;
      }

      .ghost {
        border: 1px solid var(--line);
        background: var(--panel-strong);
        color: var(--ink);
        padding: 7px 10px;
        border-radius: 10px;
        font-weight: 600;
        cursor: pointer;
      }

      .history {
        border: 1px solid var(--line);
        background: rgba(255, 255, 255, 0.6);
        border-radius: 14px;
        min-height: 460px;
        max-height: calc(100vh - 230px);
        overflow: auto;
        padding: 8px;
      }

      .item {
        width: 100%;
        border: 1px solid transparent;
        background: #fff;
        border-radius: 12px;
        padding: 10px;
        margin-bottom: 8px;
        text-align: left;
        cursor: pointer;
        transition: border-color 120ms ease, transform 120ms ease, box-shadow 120ms ease;
      }

      .item:hover {
        border-color: #ffcabd;
        transform: translateY(-1px);
        box-shadow: 0 8px 18px rgba(78, 44, 22, 0.1);
      }

      .item.active {
        border-color: #ff9d88;
        background: #fff7f4;
      }

      .item-text {
        font-size: 13px;
        color: #302c25;
        line-height: 1.45;
        white-space: pre-wrap;
        word-break: break-word;
        overflow-wrap: anywhere;
        display: -webkit-box;
        -webkit-line-clamp: 3;
        -webkit-box-orient: vertical;
        overflow: hidden;
      }

      .item-time {
        margin-top: 8px;
        font-size: 11px;
        color: #8a7e6d;
      }

      .empty {
        color: var(--muted);
        font-size: 14px;
        text-align: center;
        margin-top: 24px;
      }

      .compose {
        display: grid;
        gap: 12px;
      }

      .live {
        border: 1px solid var(--line);
        border-radius: 14px;
        background: rgba(255, 255, 255, 0.66);
        min-height: 120px;
        padding: 14px;
        font-size: 14px;
        line-height: 1.55;
        white-space: pre-wrap;
        word-break: break-word;
      }

      textarea {
        width: 100%;
        min-height: 280px;
        border-radius: 14px;
        border: 1px solid var(--line);
        background: rgba(255, 255, 255, 0.9);
        padding: 14px;
        color: var(--ink);
        font: inherit;
        outline: none;
        resize: vertical;
        transition: border-color 130ms ease, box-shadow 130ms ease;
      }

      textarea:focus {
        border-color: #ff967d;
        box-shadow: 0 0 0 4px rgba(255, 90, 54, 0.12);
      }

      .actions {
        display: flex;
        align-items: center;
        flex-wrap: wrap;
        gap: 10px;
      }

      .btn {
        border: none;
        border-radius: 11px;
        background: linear-gradient(135deg, var(--brand), var(--brand-2));
        color: #2a140f;
        font-weight: 800;
        padding: 11px 14px;
        cursor: pointer;
      }

      .btn:disabled {
        opacity: 0.6;
        cursor: wait;
      }

      .status {
        font-size: 13px;
        color: var(--muted);
      }

      .status.ok {
        color: var(--ok);
      }

      .status.err {
        color: var(--err);
      }

      @media (max-width: 980px) {
        .grid {
          grid-template-columns: 1fr;
          min-height: 0;
        }

        .left {
          border-right: 0;
          border-bottom: 1px solid var(--line);
        }

        .history {
          max-height: 40vh;
          min-height: 180px;
        }

        textarea {
          min-height: 220px;
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
