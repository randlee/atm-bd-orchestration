#!/usr/bin/env python3
"""Start or stop a disposable, private server-mode bd database for an eval."""
from __future__ import annotations

import json
import os
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path


def start(root: Path) -> None:
    root = root.resolve(strict=True)
    data = root / "data"
    database = data / "atm"
    database.mkdir(parents=True, exist_ok=False)
    subprocess.run(["dolt", "init"], cwd=database, check=True)
    sock = root / "dolt.sock"
    log_path = root / "dolt.log"
    process = None
    port = 0
    for _ in range(5):
        with socket.socket() as reservation:
            reservation.bind(("127.0.0.1", 0))
            port = reservation.getsockname()[1]
        with log_path.open("ab") as log:
            process = subprocess.Popen(
                ["dolt", "sql-server", "--host", "127.0.0.1", "--port", str(port),
                 "--socket", str(sock), "--data-dir", str(data)],
                cwd=root, stdout=log, stderr=subprocess.STDOUT, start_new_session=True,
            )
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            if process.poll() is not None:
                break
            if sock.exists():
                try:
                    with socket.socket(socket.AF_UNIX) as client:
                        client.connect(str(sock))
                    break
                except OSError:
                    pass
            time.sleep(0.1)
        else:
            process.terminate()
            process.wait(timeout=10)
            raise RuntimeError(f"private Dolt server did not become ready; see {log_path}")
        if process.poll() is None and sock.exists():
            break
        sock.unlink(missing_ok=True)
    else:
        raise RuntimeError(f"private Dolt server could not bind a port; see {log_path}")
    assert process is not None
    env = {**os.environ, "BEADS_DIR": str(root / ".beads")}
    try:
        subprocess.run(["bd", "init", "--server", "--server-host", "127.0.0.1",
                        "--server-port", str(port), "--server-socket", str(sock),
                        "--prefix", "atm", "--non-interactive", "--skip-hooks", "--skip-agents"],
                       cwd=root, env=env, check=True)
    except BaseException:
        process.terminate()
        process.wait(timeout=10)
        raise
    context = {"pid": process.pid, "socket": str(sock), "port": port,
               "beads_dir": str(root / ".beads"), "data_dir": str(data)}
    (root / "server.json").write_text(json.dumps(context) + "\n", encoding="utf-8")
    print(json.dumps(context))


def stop(root: Path) -> None:
    root = root.resolve(strict=True)
    context = json.loads((root / "server.json").read_text(encoding="utf-8"))
    pid = context["pid"]
    sock = str(root / "dolt.sock")
    if context["socket"] != sock or context["data_dir"] != str(root / "data"):
        raise RuntimeError("server context does not belong to this scratch directory")
    command = subprocess.run(["ps", "-p", str(pid), "-o", "command="],
                             capture_output=True, text=True, check=False)
    if command.returncode == 0:
        if sock not in command.stdout or str(root / "data") not in command.stdout:
            raise RuntimeError("server PID no longer identifies this private Dolt server")
        os.kill(pid, signal.SIGTERM)
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            state = subprocess.run(["ps", "-p", str(pid), "-o", "stat="],
                                   capture_output=True, text=True, check=False)
            if state.returncode != 0 or state.stdout.strip().startswith("Z"):
                break
            time.sleep(0.1)
        else:
            raise RuntimeError("private Dolt server did not stop; retain its database")
    print(f"stopped private server {pid}")


if __name__ == "__main__":
    if len(sys.argv) != 3 or sys.argv[1] not in {"start", "stop"}:
        raise SystemExit("usage: db-server.py start|stop <scratch-directory>")
    (start if sys.argv[1] == "start" else stop)(Path(sys.argv[2]))
