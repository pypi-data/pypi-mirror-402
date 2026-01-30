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

import tempfile
import signal
import time

from collections import deque
from dataclasses import dataclass
from enum        import Enum, auto
from hashlib     import md5
from pathlib     import Path
from subprocess  import Popen


class JobStatus(Enum):
    QUEUED = auto()
    RUNNING = auto()
    SUCCEEDED = auto()
    FAILED = auto()
    CANCELLED = auto()

@dataclass
class JobState:
    # Job's uid
    uid : str
    # Current status of the job
    status : JobStatus=JobStatus.QUEUED
    start=None
    end=None

    @property
    def runtime(self) -> float | None:
        if self.start is None:
            return None
        if self.end is None:
            return time.time() - self.start
        return self.end - self.start
    
    def start_job(self):
        self.start = time.time()
        self.status = JobStatus.RUNNING
    
    def stop_job(self, exit_status : JobStatus):
        if exit_status == JobStatus.RUNNING:
            raise ValueError('Cannot exit a job with RUNNING status.')

        self.end = time.time()
        self.status = exit_status

    def set_cancelled(self):
        if self.status == JobStatus.RUNNING:
            self.stop_job(JobStatus.CANCELLED)
        else:
            self.status = JobStatus.CANCELLED

    def reset(self):
        self.start  = None
        self.end    = None
        self.status = JobStatus.QUEUED


class Job:
    def __init__(self, cmd : list[str], cwd : Path=None):
        self._cmd = cmd
        self._cwd  = cwd if cwd is not None else Path('.').absolute()
        self._hash = md5((f'CWD:={self._cwd}' + ' '.join([str(a) for a in cmd])).encode()).hexdigest()[:8]
        self._proc = None
        self._returncode = None

        self._tmpdir = None
        self._stdout_path = None
        self._stderr_path = None

    @property
    def uid(self) -> str:
        return self._hash
    
    @property
    def pid(self) -> int | None:
        if self._proc is not None:
            return self._proc.pid
        return None

    def __hash__(self):
        return hash(self._hash)

    def start(self):
        self._tmpdir = Path(tempfile.mkdtemp(prefix="jobrunner_"))
        self._stdout_path = self._tmpdir / "stdout.log"
        self._stderr_path = self._tmpdir / "stderr.log"

        self._stdout = open(self._stdout_path, "wb")
        self._stderr = open(self._stderr_path, "wb")

        self._proc = Popen(self._cmd,
                          stdout=self._stdout,
                          stderr=self._stderr,
                          cwd=str(self._cwd))

    def _send_signal(self, signal):
        if self._proc:
            self._proc.send_signal(signal)

    def kill(self):
        self._send_signal(signal.SIGKILL)

    def wait(self):
        if self._proc is not None:
            self._proc.wait()
            self.finalize()

    def interrupt(self):
        self._send_signal(signal.SIGINT)

    def poll(self):
        if self._proc:
            self._returncode = self._proc.poll()
        return self._returncode

    def finalize(self):
        self._stdout.close()
        self._stderr.close()


class JobManager:
    def __init__(self, jobs : list[Job]=None, n_processes=100):
        self._all_jobs  = {}  # type: dict[str, Job]
        self._queue     = deque() # type: deque[str]
        self._job_state = {}  # type: dict[str, JobState]
        self._n_processes = n_processes

        if jobs is not None:
            for j in jobs:
                self.queue_job(j)

    def _get_jobs_by_status(self, status) -> dict[str, Job]:
        job_ids = [uid for uid, state in self._job_state.items() if state.status == status]
        return {uid: self._all_jobs[uid] for uid in job_ids}

    @property
    def succeded_jobs(self) -> dict[str, Job]:
        return self._get_jobs_by_status(JobStatus.SUCCEEDED)

    @property
    def failed_jobs(self) -> dict[str, Job]:
        return self._get_jobs_by_status(JobStatus.FAILED)
    
    @property
    def running_jobs(self) -> dict[str, Job]:
        return self._get_jobs_by_status(JobStatus.RUNNING)
    
    @property
    def queued_jobs(self) -> dict[str, Job]:
        return self._get_jobs_by_status(JobStatus.QUEUED)
    
    @property
    def cancelled_jobs(self) -> dict[str, Job]:
        return self._get_jobs_by_status(JobStatus.CANCELLED)
    
    @property
    def is_done(self) -> bool:
        return not any([s.status in {JobStatus.RUNNING, JobStatus.QUEUED} for s in self._job_state.values()])

    @property
    def n_jobs_left(self) -> bool:
        return sum([int(s.status in {JobStatus.RUNNING, JobStatus.QUEUED}) for s in self._job_state.values()])

    def queue_job(self, job : Job):
        if job.uid not in self._all_jobs:
            self._all_jobs[job.uid]  = job
            self._job_state[job.uid] = JobState(job.uid)
        else:
            match self._job_state[job.uid].status:
                # Job is known and already in queue
                case JobStatus.QUEUED:
                    return
                # Job is currently running, so nothing to do here
                case JobStatus.RUNNING:
                    return
                case _:
                    pass

        self._job_state[job.uid].reset()
        self._queue.append(job.uid)

    def cancel_job(self, job : Job | str):
        job = job.uid if isinstance(job, Job) else job
        if job not in self._all_jobs:
            raise KeyError(f'Unknown job {job}')
        
        state = self._job_state[job]
        match state.status: 
            case JobStatus.RUNNING:
                j = self._all_jobs[job]
                j.kill()
                j.wait()
                state.stop_job(JobStatus.CANCELLED)
            case JobStatus.QUEUED:
                self._queue.remove(job)
                state.set_cancelled()
            case _:
                pass
    
    def tick(self):
        n_running = 0
        for uid, j in self.running_jobs.items():
            if (ret_val:=j.poll()) is not None: # Job has returned
                j.finalize()
                state = self._job_state[uid]
                state.stop_job(JobStatus.SUCCEEDED if ret_val == 0 else JobStatus.FAILED)
            else:
                n_running += 1

        # Start new jobs if we have capacity        
        for x in range(self._n_processes - n_running):
            try:
                next_uid = self._queue.popleft()
                job = self._all_jobs[next_uid]
                # Kicking off the subprocess
                job.start()
                # Updating its state
                state = self._job_state[next_uid]
                state.start_job()
            except IndexError:
                pass

    def kill(self, and_wait=True):
        """Kill all jobs"""
        for uid, j in self._all_jobs.items():
            j.kill()
            self._job_state[uid].set_cancelled()
        
        if and_wait:
            for j in self._all_jobs.values():
                j.wait()
