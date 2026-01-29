# Copyright (c) 2026 Adrian Röfer
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.


import argparse
import json
import os
import subprocess
import time
from pathlib import Path
from urllib.parse import urlparse
from urllib.error import URLError
from urllib.request import Request, urlopen

from .utils import parse_job_spec, parse_task_file  # adjust import


def ensure_server_running(server_cmd: list[str], server_url="http://127.0.0.1:5678", timeout=10):
    """
    Check if server is alive; if not, start it as a detached process.
    `server_cmd` should be e.g. ["python", "-m", "roejobs.server"]
    """

    try:
        with urlopen(f"{server_url}/jobs", timeout=1):
            return
    except URLError:
        print("Server not found, launching in background...")

        parsed_url = urlparse(server_url)
        port = parsed_url.port or 5678

        server_proc = subprocess.Popen(
            server_cmd + ["--port", str(port)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )

        # Wait until server responds or timeout
        start = time.time()
        while True:
            try:
                with urlopen(f"{server_url}/jobs", timeout=1):
                    print(f"Server is up! PID is: {server_proc.pid}")
                    return
            except URLError:
                if time.time() - start > timeout:
                    raise RuntimeError("Failed to start server in time")
                time.sleep(0.5)


def submit_job(server_url, cmd, cwd):
    payload = {"cmd": cmd}
    if cwd is not None:
        payload["cwd"] = str(cwd)

    req = Request(
        f"{server_url}/jobs",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urlopen(req) as resp:
        return json.loads(resp.read())


def submit_job(server_url, cmd, cwd):
    payload = {"cmd": cmd}
    if cwd is not None:
        payload["cwd"] = str(cwd)

    req = Request(
        f"{server_url}/jobs",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urlopen(req) as resp:
        return json.loads(resp.read())

SERVER_CMD = ["python", "-m", "roejobs.server"]

def main():
    parser = argparse.ArgumentParser(description="Submit jobs to jobrunner")

    parser.add_argument(
        "files",
        nargs="*",
        type=Path,
        help="Task files (one job per line)",
    )

    parser.add_argument(
        "--jobs",
        nargs="*",
        default=[],
        metavar="SPEC",
        help="Job specs (same syntax as task files)",
    )

    parser.add_argument(
        "--override-cwd",
        action="store_true",
        help="Ignore CWD=... and use current working directory",
    )

    parser.add_argument(
        "--server",
        default="http://127.0.0.1:5678",
        help="Jobrunner server URL",
    )

    args = parser.parse_args()

    jobs = []

    # Jobs from files
    for file in args.files:
        jobs.extend(parse_task_file(file))

    # Jobs from CLI
    for spec in args.jobs:
        job = parse_job_spec(spec)
        if job:
            jobs.append(job)

    if not jobs:
        print("No jobs to submit.")
        return

    # Override CWD if requested
    if args.override_cwd:
        cwd = Path(os.getcwd()).resolve()
        for job in jobs:
            job["cwd"] = cwd

    ensure_server_running(SERVER_CMD, args.server, timeout=10)

    # Submit
    for job in jobs:
        result = submit_job(
            args.server,
            cmd=job["cmd"],
            cwd=job["cwd"],
        )
        cmd_str = " ".join(job["cmd"])
        cwd_str = f" (cwd={job['cwd']})" if job["cwd"] else ""
        print(f"Queued {result['uid']}: {cmd_str}{cwd_str}")
