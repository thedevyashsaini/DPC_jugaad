from __future__ import annotations

import argparse
import asyncio
import json
import os
import random
import shlex
import subprocess
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
DEFAULT_SERVICE_NAME = "clipboard-fleet-agent"
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


def run_command(
    args: list[str], check: bool = True, capture: bool = False
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        check=check,
        text=True,
        capture_output=capture,
    )


def command_for_display(args: list[str]) -> str:
    if os.name == "nt":
        return subprocess.list2cmdline(args)
    return shlex.join(args)


def build_agent_exec_args(poll: float) -> list[str]:
    script_path = str(Path(__file__).resolve())
    return [sys.executable, script_path, "run", "--poll", str(poll)]


def require_joined_state() -> dict[str, Any] | None:
    state = load_state()
    if not state:
        print(
            "No joined device state found. Run: abc join --server <url> --token <token>"
        )
        return None
    return state


def linux_service_path(name: str) -> Path:
    return Path.home() / ".config" / "systemd" / "user" / f"{name}.service"


def install_linux_service(name: str, poll: float) -> int:
    if require_joined_state() is None:
        return 1

    unit_path = linux_service_path(name)
    unit_path.parent.mkdir(parents=True, exist_ok=True)
    exec_args = build_agent_exec_args(poll)
    exec_line = " ".join(shlex.quote(x) for x in exec_args)
    workdir = shlex.quote(str(Path(__file__).resolve().parent))
    unit_text = (
        "[Unit]\n"
        "Description=Clipboard Fleet Agent\n"
        "After=network-online.target\n"
        "Wants=network-online.target\n\n"
        "[Service]\n"
        "Type=simple\n"
        f"WorkingDirectory={workdir}\n"
        f"ExecStart={exec_line}\n"
        "Restart=always\n"
        "RestartSec=2\n"
        "Environment=PYTHONUNBUFFERED=1\n\n"
        "[Install]\n"
        "WantedBy=default.target\n"
    )
    unit_path.write_text(unit_text, encoding="utf-8")

    run_command(["systemctl", "--user", "daemon-reload"])
    run_command(["systemctl", "--user", "enable", "--now", f"{name}.service"])
    print(f"Installed and started user service: {name}")
    print(f"Unit file: {unit_path}")
    print("To start even before interactive login, run: loginctl enable-linger $USER")
    return 0


def install_windows_service(name: str, poll: float) -> int:
    if require_joined_state() is None:
        return 1

    exec_args = build_agent_exec_args(poll)
    task_cmd = command_for_display(exec_args)
    run_command(
        [
            "schtasks",
            "/Create",
            "/TN",
            name,
            "/SC",
            "ONLOGON",
            "/TR",
            task_cmd,
            "/F",
        ]
    )
    run_command(["schtasks", "/Run", "/TN", name], check=False)
    print(f"Installed and started scheduled task: {name}")
    print("Task trigger: ONLOGON (starts automatically after reboot when user logs in)")
    return 0


def start_linux_service(name: str) -> int:
    run_command(["systemctl", "--user", "start", f"{name}.service"])
    print(f"Started service: {name}")
    return 0


def stop_linux_service(name: str) -> int:
    run_command(["systemctl", "--user", "stop", f"{name}.service"])
    print(f"Stopped service: {name}")
    return 0


def status_linux_service(name: str) -> int:
    result = run_command(
        ["systemctl", "--user", "status", f"{name}.service", "--no-pager"],
        check=False,
        capture=True,
    )
    output = (result.stdout or "") + (result.stderr or "")
    print(output.strip() or f"No status output for {name}")
    return 0 if result.returncode == 0 else 1


def uninstall_linux_service(name: str) -> int:
    run_command(
        ["systemctl", "--user", "disable", "--now", f"{name}.service"], check=False
    )
    unit_path = linux_service_path(name)
    if unit_path.exists():
        unit_path.unlink()
    run_command(["systemctl", "--user", "daemon-reload"], check=False)
    print(f"Uninstalled service: {name}")
    return 0


def start_windows_service(name: str) -> int:
    run_command(["schtasks", "/Run", "/TN", name])
    print(f"Started task: {name}")
    return 0


def stop_windows_service(name: str) -> int:
    run_command(["schtasks", "/End", "/TN", name], check=False)
    print(f"Stopped task: {name}")
    return 0


def status_windows_service(name: str) -> int:
    result = run_command(
        ["schtasks", "/Query", "/TN", name, "/V", "/FO", "LIST"],
        check=False,
        capture=True,
    )
    output = (result.stdout or "") + (result.stderr or "")
    print(output.strip() or f"No status output for {name}")
    return 0 if result.returncode == 0 else 1


def uninstall_windows_service(name: str) -> int:
    run_command(["schtasks", "/Delete", "/TN", name, "/F"], check=False)
    print(f"Uninstalled task: {name}")
    return 0


def cmd_service_install(args: argparse.Namespace) -> int:
    try:
        if os.name == "nt":
            return install_windows_service(args.name, args.poll)
        return install_linux_service(args.name, args.poll)
    except FileNotFoundError as exc:
        print(f"Missing platform command: {exc}")
        return 1
    except subprocess.CalledProcessError as exc:
        print(f"Service install failed (exit {exc.returncode}): {exc}")
        return 1


def cmd_service_start(args: argparse.Namespace) -> int:
    try:
        if os.name == "nt":
            return start_windows_service(args.name)
        return start_linux_service(args.name)
    except subprocess.CalledProcessError as exc:
        print(f"Service start failed (exit {exc.returncode}): {exc}")
        return 1


def cmd_service_stop(args: argparse.Namespace) -> int:
    try:
        if os.name == "nt":
            return stop_windows_service(args.name)
        return stop_linux_service(args.name)
    except subprocess.CalledProcessError as exc:
        print(f"Service stop failed (exit {exc.returncode}): {exc}")
        return 1


def cmd_service_status(args: argparse.Namespace) -> int:
    if os.name == "nt":
        return status_windows_service(args.name)
    return status_linux_service(args.name)


def cmd_service_uninstall(args: argparse.Namespace) -> int:
    try:
        if os.name == "nt":
            return uninstall_windows_service(args.name)
        return uninstall_linux_service(args.name)
    except subprocess.CalledProcessError as exc:
        print(f"Service uninstall failed (exit {exc.returncode}): {exc}")
        return 1


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
    state = require_joined_state()
    if not state:
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


def cmd_nuke(args: argparse.Namespace) -> int:
    wipe_tokens = bool(args.tokens)
    wipe_devices = bool(args.devices)
    if not wipe_tokens and not wipe_devices:
        wipe_tokens = True
        wipe_devices = True

    endpoint = urljoin(args.server.rstrip("/") + "/", "api/admin/nuke")
    headers = {"x-admin-token": args.admin_token}
    payload = {"tokens": wipe_tokens, "devices": wipe_devices}
    data = http_json("POST", endpoint, payload=payload, headers=headers)
    print_json(data)
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
        "--ttl",
        type=int,
        default=900,
        help="Token lifetime in seconds; use 0 for never expires",
    )
    add_p.set_defaults(func=cmd_add)

    nuke_p = sub.add_parser("nuke", help="Delete all join tokens and/or joined devices")
    nuke_p.add_argument("--server", required=True, help="Worker URL")
    nuke_p.add_argument("--admin-token", required=True, help="Admin token")
    nuke_p.add_argument("--tokens", action="store_true", help="Delete all join tokens")
    nuke_p.add_argument("--devices", action="store_true", help="Delete all devices")
    nuke_p.set_defaults(func=cmd_nuke)

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

    svc_p = sub.add_parser("service", help="Manage persistent background agent service")
    svc_sub = svc_p.add_subparsers(dest="service_command", required=True)

    svc_install = svc_sub.add_parser(
        "install",
        help="Install and start persistent agent service",
    )
    svc_install.add_argument(
        "--name",
        default=DEFAULT_SERVICE_NAME,
        help=f"Service/task name (default: {DEFAULT_SERVICE_NAME})",
    )
    svc_install.add_argument(
        "--poll",
        type=float,
        default=0.25,
        help="Clipboard poll interval in seconds",
    )
    svc_install.set_defaults(func=cmd_service_install)

    svc_start = svc_sub.add_parser("start", help="Start installed service")
    svc_start.add_argument(
        "--name",
        default=DEFAULT_SERVICE_NAME,
        help=f"Service/task name (default: {DEFAULT_SERVICE_NAME})",
    )
    svc_start.set_defaults(func=cmd_service_start)

    svc_stop = svc_sub.add_parser("stop", help="Stop installed service")
    svc_stop.add_argument(
        "--name",
        default=DEFAULT_SERVICE_NAME,
        help=f"Service/task name (default: {DEFAULT_SERVICE_NAME})",
    )
    svc_stop.set_defaults(func=cmd_service_stop)

    svc_status = svc_sub.add_parser("status", help="Show service status")
    svc_status.add_argument(
        "--name",
        default=DEFAULT_SERVICE_NAME,
        help=f"Service/task name (default: {DEFAULT_SERVICE_NAME})",
    )
    svc_status.set_defaults(func=cmd_service_status)

    svc_uninstall = svc_sub.add_parser(
        "uninstall",
        help="Uninstall persistent service",
    )
    svc_uninstall.add_argument(
        "--name",
        default=DEFAULT_SERVICE_NAME,
        help=f"Service/task name (default: {DEFAULT_SERVICE_NAME})",
    )
    svc_uninstall.set_defaults(func=cmd_service_uninstall)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
