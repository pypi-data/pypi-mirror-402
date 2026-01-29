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


import json
import threading
import time
from argparse     import ArgumentParser
from datetime     import datetime
from http.server  import BaseHTTPRequestHandler, HTTPServer
from jinja2       import Environment, FileSystemLoader, select_autoescape
from pathlib      import Path
from urllib.parse import urlparse


from .jobs import Job, JobManager, JobStatus  


class JobServer:
    def __init__(self, manager: JobManager, host="127.0.0.1", port=8080, tick_interval=0.5):
        self.manager = manager
        self.host = host
        self.port = port
        self.tick_interval = tick_interval
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._httpd = None

        template_dir = Path(__file__).parent / "templates"
        self.jinja = Environment(loader=FileSystemLoader(template_dir),
                                 autoescape=select_autoescape(["html"]))

    # ------------------------
    # Scheduler loop
    # ------------------------
    def _scheduler_loop(self):
        while not self._stop_event.is_set():
            with self._lock:
                self.manager.tick()
            time.sleep(self.tick_interval)

    # ------------------------
    # HTTP server
    # ------------------------
    def serve(self):
        server = self

        class Handler(BaseHTTPRequestHandler):
            def _json_response(self, code, payload):
                body = json.dumps(payload).encode()
                self.send_response(code)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def _read_json(self):
                length = int(self.headers.get("Content-Length", 0))
                if length == 0:
                    return {}
                return json.loads(self.rfile.read(length))

            def _redirect(self, location="/"):
                self.send_response(303)
                self.send_header("Location", location)
                self.end_headers()

            def _read_text_file(self, path: Path, max_bytes=5_000_000):
                if not path.exists():
                    return ""
                data = path.read_bytes()
                if len(data) > max_bytes:
                    data = data[-max_bytes:]
                return data.decode(errors="replace")

            def do_GET(self):
                parsed = urlparse(self.path)
                parts = parsed.path.strip("/").split("/")

                with server._lock:
                    if parsed.path == '/':
                        template = server.jinja.get_template("jobs.html")

                        jobs = []
                        for uid, state in server.manager._job_state.items():
                            job = server.manager._all_jobs[uid]
                            jobs.append({
                                "uid": uid,
                                "status": state.status.name,
                                "runtime": state.runtime,
                                "pid": job.pid,
                                "cmd": " ".join(job._cmd),
                            })

                        html = template.render(
                            jobs=jobs,
                            now=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        ).encode()

                        self.send_response(200)
                        self.send_header("Content-Type", "text/html; charset=utf-8")
                        self.send_header("Content-Length", str(len(html)))
                        self.end_headers()
                        self.wfile.write(html)
                        return

                    if parsed.path == "/health":
                        self._json_response(200, {"status": "ok"})
                        return

                    if len(parts) == 2 and parts[0] == "jobs":
                        uid = parts[1]
                        if uid not in server.manager._job_state:
                            self._json_response(404, {"error": "unknown job"})
                            return

                        state = server.manager._job_state[uid]
                        job = server.manager._all_jobs[uid]

                        template = server.jinja.get_template("job_detail.html")
                        html = template.render(
                            job={
                                "uid": uid,
                                "status": state.status.name,
                                "runtime": state.runtime,
                                "pid": job.pid,
                                "cmd": " ".join(job._cmd),
                            }
                        ).encode()

                        self.send_response(200)
                        self.send_header("Content-Type", "text/html; charset=utf-8")
                        self.send_header("Content-Length", str(len(html)))
                        self.end_headers()
                        self.wfile.write(html)
                        return

                    if len(parts) == 3 and parts[0] == "jobs" and parts[2] == "stdout":
                        uid = parts[1]
                        job = server.manager._all_jobs.get(uid)
                        if not job or not job._stdout_path:
                            self._json_response(404, {"error": "log not available"})
                            return

                        content = self._read_text_file(job._stdout_path)
                        template = server.jinja.get_template("log_view.html")
                        html = template.render(
                            title=f"stdout — {uid}",
                            uid=uid,
                            content=content,
                        ).encode()

                        self.send_response(200)
                        self.send_header("Content-Type", "text/html; charset=utf-8")
                        self.send_header("Content-Length", str(len(html)))
                        self.end_headers()
                        self.wfile.write(html)
                        return

                    if len(parts) == 3 and parts[0] == "jobs" and parts[2] == "stderr":
                        uid = parts[1]
                        job = server.manager._all_jobs.get(uid)
                        if not job or not job._stderr_path:
                            self._json_response(404, {"error": "log not available"})
                            return

                        content = self._read_text_file(job._stderr_path)
                        template = server.jinja.get_template("log_view.html")
                        html = template.render(
                            title=f"stderr — {uid}",
                            uid=uid,
                            content=content,
                        ).encode()

                        self.send_response(200)
                        self.send_header("Content-Type", "text/html; charset=utf-8")
                        self.send_header("Content-Length", str(len(html)))
                        self.end_headers()
                        self.wfile.write(html)
                        return

                    if parsed.path == "/jobs":
                        jobs = {uid: {"status": state.status.name,
                                      "runtime": state.runtime,
                                      "pid": server.manager._all_jobs[uid].pid}
                            for uid, state in server.manager._job_state.items()
                        }
                        self._json_response(200, jobs)
                        return

                    if len(parts) == 2 and parts[0] == "jobs":
                        uid = parts[1]
                        if uid not in server.manager._job_state:
                            self._json_response(404, {"error": "unknown job"})
                            return

                        state = server.manager._job_state[uid]
                        job = server.manager._all_jobs[uid]

                        self._json_response(200, {"uid": uid,
                                                  "status": state.status.name,
                                                  "runtime": state.runtime,
                                                  "pid": job.pid})
                        return

                self._json_response(404, {"error": "not found"})

            def do_POST(self):
                parsed = urlparse(self.path)
                parts = parsed.path.strip("/").split("/")

                with server._lock:
                    # -------------------------
                    # Cancel job (HTML)
                    # -------------------------
                    if len(parts) == 3 and parts[0] == "jobs" and parts[2] == "cancel":
                        uid = parts[1]
                        try:
                            server.manager.cancel_job(uid)
                        except KeyError:
                            pass
                        self._redirect("/")
                        return

                    # -------------------------
                    # Restart job (HTML)
                    # -------------------------
                    if len(parts) == 3 and parts[0] == "jobs" and parts[2] == "restart":
                        uid = parts[1]
                        if uid in server.manager._all_jobs:
                            job = server.manager._all_jobs[uid]
                            server.manager.queue_job(job)
                        self._redirect("/")
                        return

                    # -------------------------
                    # JSON API (unchanged)
                    # -------------------------
                    if parsed.path == "/jobs":
                        data = self._read_json()
                        cmd = data.get("cmd")
                        cwd = data.get("cwd")

                        if not isinstance(cmd, list):
                            self._json_response(400, {"error": "cmd must be list"})
                            return

                        job = Job(cmd, cwd=cwd)
                        server.manager.queue_job(job)

                        self._json_response(201, {"uid": job.uid})
                        return
                    
                    # -------------------------
                    # Shutdown server
                    # -------------------------
                    if parsed.path == "/shutdown":
                        # Immediately respond with redirect
                        self.send_response(302)
                        self.send_header("Location", "/")
                        self.end_headers()

                        # Shutdown in a separate thread to avoid deadlock
                        threading.Thread(target=server.shutdown, daemon=True).start()
                        return

                self._json_response(404, {"error": "not found"})

            def log_message(self, fmt, *args):
                # Silence default logging (optional)
                pass

        self._httpd = HTTPServer((self.host, self.port), Handler)

        scheduler = threading.Thread(target=self._scheduler_loop, daemon=True)
        scheduler.start()

        try:
            print(f"Job server listening on http://{self.host}:{self.port}")
            self._httpd.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            self._stop_event.set()
            with self._lock:
                self.manager.kill()
            self._httpd.server_close()

    def shutdown(self):
        print("Shutting down jobrunner server...")

        self._stop_event.set()

        with self._lock:
            self.manager.kill(and_wait=True)

        if self._httpd:
            self._httpd.shutdown()


def main():
    parser = ArgumentParser(description='Roejobs Job server -- To serve you!')
    parser.add_argument('--port', type=int, default=5678, help='Port the server listens on.')
    parser.add_argument('--n-processes', type=int, default=10, help='Maximum number of jobs to run simultaneously.')
    args = parser.parse_args()
    manager = JobManager(n_processes=args.n_processes)
    server = JobServer(manager, port=args.port)
    server.serve()


if __name__ == '__main__':
    main()
