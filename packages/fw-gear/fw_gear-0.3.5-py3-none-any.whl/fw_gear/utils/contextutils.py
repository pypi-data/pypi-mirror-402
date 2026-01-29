import csv
import functools
import logging
import os
import shutil
import subprocess
import tempfile
import time
import typing as t
from contextlib import contextmanager
from multiprocessing import Manager, Process
from multiprocessing.managers import EventProxy
from pathlib import Path

try:
    import psutil
except ImportError:
    psutil = None

try:
    import requests
    import urllib3
except ImportError:
    requests = None
    urllib3 = None

try:
    import numpy as np
    import pandas as pd
    from matplotlib import pyplot as plt
except ImportError:
    np = None
    pd = None
    plt = None

log = logging.getLogger(__name__)


# Not really a testable unit since I'd need an instantiated client,
#  Good candidate for future integration test.
@contextmanager
def sdk_post_retry_handler(client):  # pragma: no cover  # noqa: PLC0415
    """Patch the SDK session object to retry on specific errors

    Safe to use on:
        - updating container info
        - updating file classification
        - adding notes
        - adding tags

    Not safe to use on:
        - Creating containers
        - Uploading files
    """
    if not requests or not urllib3:
        raise ImportError("requests and urllib3 are required for SDK retry handler")

    orig_adapter = client.api_client.rest_client.session.adapters["https://"]
    try:
        BACKOFF_FACTOR = float(os.getenv("FLYWHEEL_SDK_BACKOFF_FACTOR", 0.5))  # noqa: PLW1508
        retry = urllib3.util.Retry(
            total=5,
            backoff_factor=BACKOFF_FACTOR,
            allowed_methods=["DELETE", "GET", "HEAD", "POST", "PUT", "OPTIONS"],
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = requests.adapters.HTTPAdapter(max_retries=retry)
        client.api_client.rest_client.session.mount("http://", adapter)
        client.api_client.rest_client.session.mount("https://", adapter)
        yield
    finally:
        client.api_client.rest_client.session.mount("https://", orig_adapter)
        client.api_client.rest_client.session.mount("http://", orig_adapter)


@contextmanager
def sdk_delete_404_handler(client):
    """Ignore 404 errors on retries of deletes."""
    orig_resp_hook = client.api_client.rest_client.session.hooks["response"]
    try:

        def ignore_404(self, resp, *args, **kwargs):
            if resp.status_code == 404:
                log.debug("Ignoring 404 response on {req.method} {req.url}")
            else:
                orig_resp_hook(self, resp, *args, *kwargs)

        client.api_client.rest_client.session.hooks["response"] = ignore_404
        yield
    finally:
        client.api_client.rest_client.session.hooks["response"] = orig_resp_hook


def report_open_fds(sockets_only):
    """Decorator which reports on number of open file
        descriptors before and after a function.

    Args:
        sockets_only (bool): Report on only sockets, or all open FDs.
    """

    def wrap(func):
        # Report on open sockets
        def wrapper(*args, **kwargs):
            # Get number of open fds before function
            pid = os.getpid()
            p_args = ["lsof", "-a", "-p", str(pid)]
            if sockets_only:
                p_args.insert(1, "-i")
            ps = subprocess.Popen(p_args, stdout=subprocess.PIPE)
            before = (
                subprocess.check_output(("wc", "-l"), stdin=ps.stdout)
                .decode("utf-8")
                .strip("\r\n")
            )
            func(*args, **kwargs)
            ps = subprocess.Popen(p_args, stdout=subprocess.PIPE)
            after = (
                subprocess.check_output(("wc", "-l"), stdin=ps.stdout)
                .decode("utf-8")
                .strip("\r\n")
            )

            log.debug(
                f"Number of fds ({func.__name__}) before: {before}, after: {after}"
            )

        return wrapper

    return wrap


def report_usage_stats(
    interval: float = 1.0,
    save_output: bool = False,
    plot: bool = True,
    save_dir: str = "/flywheel/v0/output",
    cpu_usage: bool = True,
    disk_usage: bool = True,
    mem_usage: bool = True,
    net_usage: bool = True,
    disk_monitor_dirs: t.Optional[t.List[str]] = None,
    output_format: t.Optional[str] = None,
) -> t.Callable:
    """Decorator to report on resource usage during a function.

    Optional configuration to:

    * Change the update interval,
    * Turn off certain usage measurements
    * Adjust outputs save location
    * Adjust output types
    * Adjust which disk locations are monitored for disk usage.

    """

    def wrap(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # spawn subprocess that tracks cpu usage

            save_file = Path(save_dir) / f"{str(func.__name__)}"
            nonlocal disk_monitor_dirs
            if not disk_monitor_dirs:
                disk_monitor_dirs = ["/"]
            process, finished, path = _setup_usage_stats_worker(
                interval,
                cpu_usage,
                disk_usage,
                disk_monitor_dirs,
                mem_usage,
                net_usage,
            )
            func(*args, **kwargs)
            _finish_usage_stats_worker(
                process, finished, path, save_file, plot, output_format
            )

        return wrapper

    return wrap


def _setup_usage_stats_worker(
    interval: float,
    cpu_usage: bool,
    disk_usage: bool,
    disk_usage_monitor_dirs: t.List[str],
    mem_usage: bool,
    net_usage: bool,
) -> t.Tuple[Process, EventProxy, Path]:
    """Helper function to setup the usage stats worker."""
    fd, path = tempfile.mkstemp()
    os.close(fd)
    manager = Manager()
    finished = manager.Event()
    process = Process(
        target=_usage_stats_worker,
        args=(
            finished,
            interval,
            cpu_usage,
            disk_usage,
            disk_usage_monitor_dirs,
            mem_usage,
            net_usage,
            Path(path).resolve(),
        ),
    )
    process.start()
    return process, finished, path


def _finish_usage_stats_worker(  # noqa: PLC0415
    process: Process,
    finished: EventProxy,
    saved_path: Path,
    save_output: t.Optional[Path],
    plot: bool,
    output_format: t.Optional[str],
):
    """Helper function to finish the usage stats worker, and handle outputs."""
    # Terminate process by setting "finished" event.
    finished.set()
    process.join()
    # close JSON list.
    if not pd or not plt or not np:
        log.warning("Install pandas and matplotlib to view usage stats.")
        return
    df = pd.read_csv(saved_path)
    if save_output:
        df.to_csv(str(save_output) + ".csv")
    if plot:

        def _plot_size(nums):
            guess = int(np.sqrt(nums))
            if (guess**2) < nums:
                if (guess + 1) * guess < nums:
                    return guess + 1, guess + 1
                else:
                    return guess, guess + 1
            return guess, guess

        times = df["time"]
        vals = df.drop(["time"], axis=1)
        num_subplots = len([c for c in vals.columns if "total" not in c])
        rows, cols = _plot_size(num_subplots)

        fig, ax = plt.subplots(
            rows, cols, figsize=(3 * rows + 3, 2 * cols + 2), constrained_layout=True
        )
        ax = ax.ravel()
        idx = 0
        for column in vals.columns:
            if "total" in column:
                continue
            if "disk" in column:
                total_name = column.replace(
                    f"{'used' if 'used' in column else 'free'}", "total"
                )
                ax[idx].plot(times, vals[total_name], "--")
                ax[idx].plot(times, vals[column])
                ax[idx].set_ylabel("GB")
                ax[idx].set_ylim([0, vals[total_name][0] * 1.2])
            elif "mem" in column:
                ax[idx].plot(times, vals["mem_total"], "--")
                ax[idx].plot(times, vals[column])
                ax[idx].set_ylabel("GB")
                ax[idx].set_ylim([0, vals["mem_total"][0] * 1.2])
            elif "cpu" in column:
                ax[idx].set_ylabel("%")
                ax[idx].plot(times, vals[column])
                ax[idx].set_ylim([0, 100])
            elif column in ["net_sent", "net_received"]:
                ax[idx].plot(times[:-1], np.diff(vals[column]))
                ax[idx].set_ylabel("MB")
            ax[idx].set_title(column.replace(".", "/"), pad=20)
            idx += 1

        if output_format:
            fig.savefig(f"{save_output}.{output_format}", format=output_format)
        else:
            fig.savefig(f"{save_output}.png", format="png")


def _usage_stats_worker(
    finished: EventProxy,
    interval: float,
    cpu_usage: bool,
    disk_usage: bool,
    disk_usage_monitor_dirs: t.List[str],
    mem_usage: bool,
    net_usage: bool,
    save_file: Path,
) -> None:
    """Periodically monitor system usage on particular resources."""
    if not psutil and (cpu_usage or mem_usage or net_usage):
        raise ImportError(
            "psutil is required to collect CPU, memory, or network usage stats. "
            "Please install it before running this function."
        )

    counter: float = 0.0
    initial = True
    header = []
    mb_scale = 1024**2
    gb_scale = 1024**3

    def write(row: t.List[t.Any]):
        with open(save_file, "a+") as fp:
            writer = csv.writer(fp)
            writer.writerow(row)

    while not finished.is_set():
        entry = {"time": counter}
        if disk_usage:
            for path in disk_usage_monitor_dirs:
                disk = shutil.disk_usage(path)
                safe_path = str(path).replace("/", ".")
                entry[f"{safe_path}_disk_total"] = disk[0] / gb_scale
                entry[f"{safe_path}_disk_used"] = disk[1] / gb_scale
        if cpu_usage:
            cpu = psutil.cpu_percent()
            entry["cpu_usage"] = cpu
        if mem_usage:
            mem = psutil.virtual_memory()
            entry["mem_total"] = mem.total / gb_scale
            entry["mem_used"] = (mem.total / gb_scale) - (mem.available / gb_scale)
        if net_usage:
            net = psutil.net_io_counters()
            entry["net_sent"] = net.bytes_sent / mb_scale
            entry["net_received"] = net.bytes_recv / mb_scale
        if initial:
            row = list(entry.keys())
            header = row
            write(row)
            initial = False
        else:
            row = [entry[key] for key in header]
            write(row)

        counter += interval
        time.sleep(interval)
