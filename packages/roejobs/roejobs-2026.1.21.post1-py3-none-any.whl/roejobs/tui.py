import asyncio
import requests
from datetime import datetime

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, DataTable, Static
from textual.reactive import reactive
from textual.containers import Vertical
from textual.screen import Screen


STATUS_COLORS = {
    "QUEUED": "yellow",
    "RUNNING": "blue",
    "SUCCEEDED": "green",
    "FAILED": "red",
    "CANCELLED": "gray",
}


class StatusBar(Static):
    text = reactive("")

    def render(self):
        return self.text


class LogScreen(Screen):
    """Popup screen to show logs."""
    BINDINGS = [
        ("q", "pop_screen", "Back"),
    ]

    def __init__(self, title: str, content: str):
        super().__init__()
        self.title = title
        self.content = content

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        yield Static(self.content, expand=True)
        yield Footer()


class TUI(App):
    CSS = """
    DataTable {
        height: 1fr;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("c", "cancel_job", "Cancel job"),
        ("r", "restart_job", "Restart job"),
        ("l", "view_logs", "View logs"),
        ("R", "refresh", "Refresh"),
    ]

    def __init__(self, server_url: str, refresh_interval: float = 1.0):
        super().__init__()
        self.server_url = server_url.rstrip("/")
        self.refresh_interval = refresh_interval
        self.table: DataTable | None = None
        self.status_bar: StatusBar | None = None
        self._timer = None

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield DataTable()
        yield StatusBar()
        yield Footer()

    async def on_mount(self):
        self.table = self.query_one(DataTable)
        self.status_bar = self.query_one(StatusBar)

        self.table.add_columns("UID", "Status", "PID", "Runtime (s)")
        self.table.cursor_type = "row"

        await self.refresh_jobs()
        self._timer = self.set_interval(self.refresh_interval, self.refresh_jobs)

    # -----------------------------
    # Networking helpers
    # -----------------------------

    async def _get(self, path):
        def _req():
            r = requests.get(f"{self.server_url}{path}", timeout=2)
            r.raise_for_status()
            return r.json()
        return await asyncio.to_thread(_req)

    async def _post(self, path):
        def _req():
            r = requests.post(f"{self.server_url}{path}", timeout=2)
            r.raise_for_status()
        return await asyncio.to_thread(_req)

    # -----------------------------
    # Refresh logic (cursor-safe)
    # -----------------------------

    async def refresh_jobs(self):
        table = self.table
        if table is None:
            return

        # Remember selected UID
        selected_uid = None
        if table.cursor_row is not None and table.row_count > 0:
            selected_uid = table.get_row_at(table.cursor_row)[0]

        try:
            jobs = await self._get("/jobs")
        except Exception as e:
            self.status_bar.text = f"[red]Error: {e}[/red]"
            return

        table.clear()

        uid_to_row = {}
        for uid, info in sorted(jobs.items()):
            status = info["status"]
            color = STATUS_COLORS.get(status, "white")

            runtime = (
                f"{info['runtime']:.1f}"
                if info.get("runtime") is not None
                else ""
            )

            row_key = table.add_row(
                uid,
                f"[{color}]{status}[/{color}]",
                str(info.get("pid") or ""),
                runtime,
            )
            uid_to_row[uid] = row_key

        # Restore cursor
        if selected_uid in uid_to_row:
            table.move_cursor(row=table.get_row_index(uid_to_row[selected_uid]))

        self.status_bar.text = (
            f"Connected to {self.server_url} "
            f"— updated {datetime.now().strftime('%H:%M:%S')}"
        )

    # -----------------------------
    # Actions
    # -----------------------------

    def _selected_uid(self):
        if self.table and self.table.cursor_row is not None:
            return self.table.get_row_at(self.table.cursor_row)[0]
        return None

    async def action_cancel_job(self):
        uid = self._selected_uid()
        if uid:
            await self._post(f"/jobs/{uid}/cancel")
            await self.refresh_jobs()

    async def action_restart_job(self):
        uid = self._selected_uid()
        if uid:
            await self._post(f"/jobs/{uid}/restart")
            await self.refresh_jobs()

    async def action_view_logs(self):
        uid = self._selected_uid()
        if not uid:
            return

        logs = await self._get(f"/jobs/{uid}/logs")
        content = (
            "=== STDOUT ===\n"
            + logs.get("stdout", "")
            + "\n\n=== STDERR ===\n"
            + logs.get("stderr", "")
        )

        await self.push_screen(LogScreen(f"Logs for {uid}", content))

    async def action_refresh(self):
        await self.refresh_jobs()

    async def on_key(self, key: str) -> bool:
        """Handle key events. This overrides the default key binding behavior."""
        if key == "q":
            # Check if we are in the log screen, otherwise quit
            if isinstance(self.screen, LogScreen):
                await self.screen.pop_screen()  # Pop the log screen
                return True  # Prevent the quit action in TUI
            else:
                await self.shutdown()  # Quit the app in the main screen
                return True  # Prevent any further key processing
        return False


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Roejobs TUI")
    parser.add_argument(
        "--server",
        default="http://127.0.0.1:5678",
        help="Jobrunner server URL",
    )
    parser.add_argument(
        "--refresh",
        type=float,
        default=1.0,
        help="Refresh interval in seconds",
    )
    args = parser.parse_args()

    TUI(
        server_url=args.server,
        refresh_interval=args.refresh,
    ).run()
