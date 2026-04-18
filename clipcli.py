from __future__ import annotations

import argparse
import asyncio
import json
import random
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

import pyperclip
import websockets


STATE_DIR = Path.home() / ".clipboard_fleet"
STATE_FILE = STATE_DIR / "device.json"
CLI_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/125.0.0.0 Safari/537.36 ClipboardFleetCLI/1.0"
)


def print_json(data: dict[str, Any]) -> None:
    print(json.dumps(data, indent=2, ensure_ascii=True))


def http_json(
    method: str,
    url: str,
    payload: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
) -> dict[str, Any]:
    req_headers = {
        "accept": "application/json",
        "user-agent": CLI_USER_AGENT,
    }
    if headers:
        req_headers.update(headers)

    body: bytes | None = None
    if payload is not None:
        body = json.dumps(payload, ensure_ascii=True).encode("utf-8")
        req_headers["content-type"] = "application/json"

    req = urllib.request.Request(url=url, method=method, data=body, headers=req_headers)
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        msg = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code} from {url}: {msg}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Request failed for {url}: {exc}") from exc


def load_state() -> dict[str, Any] | None:
    if not STATE_FILE.exists():
        return None
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def save_state(data: dict[str, Any]) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(
        json.dumps(data, indent=2, ensure_ascii=True), encoding="utf-8"
    )


def cmd_add(args: argparse.Namespace) -> int:
    endpoint = urljoin(args.server.rstrip("/") + "/", "api/admin/create-token")
    payload = {"name": args.name, "ttl_seconds": args.ttl}
    headers = {"x-admin-token": args.admin_token}
    data = http_json("POST", endpoint, payload=payload, headers=headers)
    print("Join command:")
    print(data.get("join_command", "(missing join command)"))
    print()
    print_json(data)
    return 0


def cmd_join(args: argparse.Namespace) -> int:
    endpoint = urljoin(args.server.rstrip("/") + "/", "api/agent/join")
    data = http_json("POST", endpoint, payload={"token": args.token})

    state = {
        "server": args.server.rstrip("/"),
        "device_id": data["device_id"],
        "device_secret": data["device_secret"],
        "ws_url": data["ws_url"],
        "name": data.get("name", "device"),
        "joined_at": time.time(),
    }
    save_state(state)
    print(f"Joined as '{state['name']}' ({state['device_id']})")
    print(f"State saved to {STATE_FILE}")
    return 0


class ClipboardAgent:
    def __init__(self, state: dict[str, Any], poll_seconds: float = 0.25):
        self.state = state
        self.poll_seconds = poll_seconds
        self.ws = None
        self.running = True
        self.last_clipboard = ""
        self.last_sent = ""

    async def run(self) -> None:
        while self.running:
            try:
                await self.connect_and_loop()
            except Exception as exc:
                print(f"[agent] disconnected: {exc}")
                await asyncio.sleep(2 + random.random() * 2)

    async def connect_and_loop(self) -> None:
        ws_url = self.state["ws_url"]
        print(f"[agent] connecting to {ws_url}")
        async with websockets.connect(
            ws_url,
            ping_interval=20,
            ping_timeout=20,
            user_agent_header=CLI_USER_AGENT,
        ) as ws:
            self.ws = ws
            print("[agent] connected")
            self.last_clipboard = self.read_clipboard_safe()
            if self.last_clipboard is not None:
                await self.send_clipboard(self.last_clipboard)

            consumer = asyncio.create_task(self.consume_messages())
            producer = asyncio.create_task(self.watch_clipboard())
            heartbeat = asyncio.create_task(self.send_heartbeat())
            done, pending = await asyncio.wait(
                {consumer, producer, heartbeat}, return_when=asyncio.FIRST_EXCEPTION
            )
            for task in pending:
                task.cancel()
            for task in done:
                err = task.exception()
                if err:
                    raise err

    def read_clipboard_safe(self) -> str:
        try:
            value = pyperclip.paste()
            return value if isinstance(value, str) else str(value)
        except pyperclip.PyperclipException:
            return ""

    def write_clipboard_safe(self, text: str) -> None:
        try:
            pyperclip.copy(text)
            self.last_clipboard = text
        except pyperclip.PyperclipException as exc:
            print(f"[agent] clipboard write failed: {exc}")

    async def send_clipboard(self, text: str) -> None:
        if not self.ws:
            return
        payload = {"type": "clipboard", "text": text}
        await self.ws.send(json.dumps(payload, ensure_ascii=True))
        self.last_sent = text

    async def send_heartbeat(self) -> None:
        while True:
            if self.ws is None:
                return
            await self.ws.send(json.dumps({"type": "heartbeat"}, ensure_ascii=True))
            await asyncio.sleep(20)

    async def watch_clipboard(self) -> None:
        while True:
            now = self.read_clipboard_safe()
            if now != self.last_clipboard:
                self.last_clipboard = now
                await self.send_clipboard(now)
            await asyncio.sleep(self.poll_seconds)

    async def consume_messages(self) -> None:
        while True:
            if self.ws is None:
                return
            raw = await self.ws.recv()
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                continue

            if payload.get("type") == "set_clipboard" and isinstance(
                payload.get("text"), str
            ):
                text = payload["text"]
                self.write_clipboard_safe(text)
                await self.send_clipboard(text)


def cmd_run(args: argparse.Namespace) -> int:
    state = load_state()
    if not state:
        print(
            "No joined device state found. Run: abc join --server <url> --token <token>"
        )
        return 1

    print(
        f"Starting clipboard agent for {state.get('name', 'device')} ({state.get('device_id')})"
    )
    try:
        asyncio.run(ClipboardAgent(state=state, poll_seconds=args.poll).run())
    except KeyboardInterrupt:
        print("Stopped.")
    return 0


def cmd_status(_: argparse.Namespace) -> int:
    state = load_state()
    if not state:
        print("No device joined yet.")
        return 1
    print_json(state)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="abc",
        description="Clipboard Fleet CLI",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    add_p = sub.add_parser("add", help="Create one-time join token as admin")
    add_p.add_argument("name", help="Human-readable device name")
    add_p.add_argument(
        "--server",
        required=True,
        help="Worker URL, ex: https://clipboard-fleet.example.workers.dev",
    )
    add_p.add_argument(
        "--admin-token", required=True, help="Admin token configured in worker secret"
    )
    add_p.add_argument(
        "--ttl", type=int, default=900, help="Token lifetime in seconds (default: 900)"
    )
    add_p.set_defaults(func=cmd_add)

    join_p = sub.add_parser("join", help="Join this machine using one-time token")
    join_p.add_argument("--server", required=True, help="Worker URL")
    join_p.add_argument("--token", required=True, help="One-time join token")
    join_p.set_defaults(func=cmd_join)

    run_p = sub.add_parser("run", help="Run local clipboard agent")
    run_p.add_argument(
        "--poll", type=float, default=0.25, help="Clipboard poll interval in seconds"
    )
    run_p.set_defaults(func=cmd_run)

    status_p = sub.add_parser("status", help="Show saved device state")
    status_p.set_defaults(func=cmd_status)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
