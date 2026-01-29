from contextlib import ContextDecorator
import signal
from threading import Event, Thread

import click
import psutil

from artefacts.cli.i18n import localise


class ProcTreeTracker(ContextDecorator):
    """
    Context manager that tracks the process tree for
    all sub-processes visible at some point by the caller thread.

    This allows to, for example, review later if there is any
    rogue thread, as we have observed with some buggy Gazebo
    management library.

    Note: This is thread-based periodic watch, so anything
    happening faster than the watch period can be missed.
    """

    def __init__(self, unsafe: bool = False, period_s: int = 1):
        self.root = psutil.Process()
        self.subs = set()
        self.unsafe = unsafe
        self.period_s = period_s
        self.stop_request = Event()
        self.loop = None

    def _run(self, root: psutil.Process, period: int, stop_request: Event) -> None:
        while not stop_request.wait(timeout=period):
            self.subs = self.subs.union(set(root.children(recursive=True)))

    def terminate(self, wait_time_s: int = 3) -> dict:
        """
        Procedure to cleanup any child process still executing as CLI exit been ordered.

        This proceeds in three stages:
        1. Send SIGTERM
        2. Wait a short time to ensure clean teardown.
        3. If any child remains after wait time, SIGKILL

        A dictionary is returned with detail of what cleanup happened if any:
          {
            "found": int,
            "terminated": int,
            "killed": int,
            "errors": int,
          }

        Two modes are available:
        - Safe mode (default): Only immediate, known sub-processes are cleaned up, recursively.
        - Unsafe mode: All PIDs found while running get cleaned up (if detected in `period_s`).

        Unsafe can be dangerous as it may int/term/kill PIDs that have been reused by the OS,
        which may happen more often with long runs (more frequent with robotics). The worst that
        can happen is to kill processes owned by the same user on the machine, so please use with
        care, at your own risks.

        References:
        - https://psutil.readthedocs.io/en/latest/#kill-process-tree
        - https://psutil.readthedocs.io/en/latest/#psutil.wait_procs
        """
        # Ensure no context expects updates
        if self.loop:
            self.stop_request.set()
            self.loop.join()
            self.loop = None

        if self.unsafe:
            # Update the list of all known sub-processes in the run, if "unsafe"
            children = self.subs.union(set(self.root.children(recursive=True)))
        else:
            # Safe mode: Just include immediate, known sub-processes.
            children = set(self.root.children(recursive=True))

        # 0. SIGINT
        for p in children:
            try:
                # Try a simple interruption
                # to give a chance to the process
                # while we review the whole set.
                p.send_signal(signal.SIGINT)
            except psutil.NoSuchProcess:
                pass
        psutil.wait_procs(children, timeout=wait_time_s)

        # 1. SIGTERM
        for p in children:
            try:
                p.terminate()
            except psutil.NoSuchProcess:
                pass

        # 2. Wait
        terminated, alive = psutil.wait_procs(children, timeout=wait_time_s)

        # 3. SIGKILL to any remaining alive thread: Forced cleanup
        errors = 0
        for p in alive:
            try:
                p.kill()
                click.echo(
                    localise(
                        "Process {proc} could not be terminated normally. Forcibly ended it.".format(
                            proc=p.pid
                        )
                    )
                )
            except Exception as e:
                errors += 1
                click.echo(
                    localise(
                        "Error in forcibly ending process {proc}. You may have to proceed manually, e.g.\n\n\t`kill {proc}`\n\nCollected error message: {error})".format(
                            proc=p.pid, error=e
                        )
                    ),
                    err=True,
                )

        # Warn on any "rogue"
        if not self.unsafe:
            others = sorted(
                [str(p.pid) for p in (self.subs - children) if psutil.pid_exists(p.pid)]
            )
            if len(others) > 0:
                click.echo(
                    localise(
                        "Warning: The following processes were related to this run, but not anymore and still running: {pids}".format(
                            pids=", ".join(others)
                        )
                    ),
                    err=True,
                )

        # Reset tracker
        self.subs = set()

        return {
            "found": len(children),
            "terminated": len(terminated),
            "killed": len(alive) - errors,
            "errors": errors,
        }

    def __enter__(self):
        """
        Simple (perhaps simplistic) single-use context manager
        """
        if self.loop:
            raise Exception(
                "Non-reusable context manager. Please exit and create another one."
            )
        self.stop_request.clear()
        self.loop = Thread(
            target=self._run,
            args=(
                self.root,
                self.period_s,
                self.stop_request,
            ),
        )
        self.loop.start()

    def __exit__(self, *exc):
        """
        On context exit, ask internal thread to stop,
        join on the thread and finish.
        """
        if self.loop:
            self.stop_request.set()
            self.loop.join()
            self.loop = None
