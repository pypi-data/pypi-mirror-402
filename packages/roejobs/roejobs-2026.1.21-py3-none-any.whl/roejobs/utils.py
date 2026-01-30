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


import re
from pathlib import Path
from shlex import split as shlex_split

JOB_SPEC_RE = re.compile(
    r"""
    ^
    (?:CWD=(?P<cwd>\S+)\s+)?   # optional CWD=...
    (?P<cmd>.+)                # command
    $
    """,
    re.VERBOSE,
)

def parse_job_spec(spec: str):
    """
    Parse a single job spec line.
    Returns: (cmd: list[str], cwd: Path | None)
    """
    spec = spec.strip()

    if not spec or spec.startswith("#"):
        return None

    m = JOB_SPEC_RE.match(spec)
    if not m:
        raise ValueError(f"Invalid job spec: {spec}")

    cwd = m.group("cwd")
    cmd = m.group("cmd")

    return {
        "cmd": shlex_split(cmd),
        "cwd": Path(cwd).expanduser().resolve() if cwd else None,
    }

def parse_task_file(path: Path):
    jobs = []
    with open(path) as f:
        for lineno, line in enumerate(f, 1):
            try:
                job = parse_job_spec(line)
            except ValueError as e:
                raise ValueError(f"{path}:{lineno}: {e}") from None

            if job:
                jobs.append(job)
    return jobs
