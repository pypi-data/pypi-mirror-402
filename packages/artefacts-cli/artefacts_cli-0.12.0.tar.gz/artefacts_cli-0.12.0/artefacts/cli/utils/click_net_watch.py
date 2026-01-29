from contextlib import ContextDecorator
from threading import Event, Thread

import psutil


# TODO Add for type checking, but currently blocked by circular dependencies.
# from artefacts.cli import Run


class ClickNetWatch(ContextDecorator):
    """
    Context manager that watches network for the running process.

    Currently only bytes-out are watched, to report to a progress bar here.
    """

    def __init__(self, bar, period: int = 1):
        """
        bar: Progress bar object. Any object responding to `update(int, str)` is accepted.
        period: Number of seconds between checks.
        """
        self.bar = bar
        self.loop = None
        self.stop_request = Event()
        self.period = period
        self.net_conf = {}
        for interface in psutil.net_if_addrs():
            for snic in psutil.net_if_addrs()[interface]:
                if snic.family != psutil.AF_LINK:
                    self.net_conf[snic.address] = {
                        "if": interface,
                        "sent": 0,
                    }

    def _run(self, bar, period: int, stop_request: Event, net_conf: dict) -> None:
        """
        Internal procedure watching network, run in a thread.

        It watches network connections for the executing process,
        selects outbound and keeps track of bytes sent over `period`.
        Each `period`, it updates the progress bar with the bytes sent
        count.

        Note: This function is part of "self" but never uses `self` on
        purpose, so the thread is "complete" at creation time. No heavy
        reason, but clean. This does not guarantee anything on multi
        threading, as shared structures like `net_conf` are not protected.
        """
        proc = psutil.Process()
        while not stop_request.wait(timeout=period):
            for conn in proc.net_connections(kind="inet"):
                try:
                    lip, _ = conn.laddr
                    interface = net_conf[lip]["if"]
                    stats = psutil.net_io_counters(pernic=True)[interface]
                    last_sent = net_conf[lip]["sent"]
                    if last_sent != 0:
                        bar.update(stats.bytes_sent - last_sent)
                    net_conf[lip]["sent"] = stats.bytes_sent
                except ValueError:
                    # Ignore other connections like Unix sockets
                    pass
                else:
                    # Ignore for now, to avoid visible crashes
                    # Possible TODO: Refine and report
                    pass

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
                self.bar,
                self.period,
                self.stop_request,
                self.net_conf,
            ),
        )
        self.loop.start()

    def __exit__(self, *exc):
        """
        On context exit, ask internal thread to stop, join on the thread and finish.

        The join should ensure pending progress bar updates get applied.
        """
        if self.loop:
            self.stop_request.set()
            self.loop.join()
            self.loop = None
