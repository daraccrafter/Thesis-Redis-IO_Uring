import sys
import os
import redis
import csv
import threading
import signal
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from util import (
    run_server,
    stop_server,
    run_benchmark,
    kill_process_on_port,
    monitor_process,
    run_strace,
)

currdir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(currdir, "redis.conf")
log_dir_path = os.path.join(currdir, "logs")
redis_log_path = os.path.join(log_dir_path, "redis.log")
csvs_dir_path = os.path.join(currdir, "csvs")
os.makedirs(csvs_dir_path, exist_ok=True)
os.makedirs(log_dir_path, exist_ok=True)
tempdir = os.path.join(currdir, "temp")
os.makedirs(tempdir, exist_ok=True)

if len(sys.argv) != 2:
    print("Arg error")
    exit(1)

request_count = int(sys.argv[1])


def  consolidate_csv(
    request_count, avg_cpu_usage, avg_memory_usage, consolidated_csv_writer
):
    csv_filename = os.path.join(csvs_dir_path, f"always_{request_count}.csv")
    syscall_filename = os.path.join(
        csvs_dir_path, f"always_{request_count}_syscalls.csv"
    )
    syscall_times_filename = os.path.join(
        csvs_dir_path, f"always_{request_count}_syscalls-times.csv"
    )

    if not os.path.exists(csv_filename):
        raise FileNotFoundError(f"Expected CSV file not found: {csv_filename}")

    with open(csv_filename, "r") as input_csv, open(
        syscall_filename, "r"
    ) as syscall_csv, open(syscall_times_filename, "r") as syscall_times_csv:

        csv_reader = csv.reader(input_csv)
        syscall_reader = csv.DictReader(syscall_csv)
        syscall_times_reader = csv.DictReader(syscall_times_csv)

        headers = next(csv_reader)

        for row in csv_reader:
            row_dict = dict(zip(headers, row))

            syscall_counts = {
                row["syscall"]: int(row["count"]) for row in syscall_reader
            }
            syscall_times = {
                row["syscall"]: row["time"] for row in syscall_times_reader
            }

            total_syscall_count = sum(syscall_counts.values())

            row_dict.update(
                {
                    "Fsync Type": "always",
                    "CPU Usage": avg_cpu_usage,
                    "Memory Usage": avg_memory_usage,
                    "fdatasync_count": syscall_counts.get("fdatasync", 0),
                    "write_count": syscall_counts.get("write", 0),
                    "io_uring_enter_count": syscall_counts.get("io_uring_enter", 0),
                    "write_time": syscall_times.get("write", 0),
                    "fdatasync_time": syscall_times.get("fdatasync", 0),
                    "io_uring_enter_time": syscall_times.get("io_uring_enter", 0),
                    "total_time": syscall_times.get("total", 0),
                    "total_syscall_count": total_syscall_count,
                }
            )

            consolidated_csv_writer.writerow(row_dict)


def run_all_tasks(r, process, request_count):
    consolidated_csv_path = os.path.join(
        csvs_dir_path, "consolidated_results_io_uring.csv"
    )
    headers_written = False
    r.config_set("save", "")
    with open(consolidated_csv_path, "w", newline="") as consolidated_csv:
        csv_writer = None

        run_benchmark(request_count, csvs_dir_path, 6382, "always")

        cpu_usages, memory_usages = [], []
        stop_event = threading.Event()
        monitor_thread = threading.Thread(
            target=monitor_process,
            args=(process.pid, stop_event, cpu_usages, memory_usages),
        )
        monitor_thread.start()
        run_benchmark(request_count, csvs_dir_path, 6382, "always", save_csv=False)
        stop_event.set()
        monitor_thread.join()

        avg_cpu_usage = sum(cpu_usages) / len(cpu_usages) if cpu_usages else 0
        avg_memory_usage = (
            sum(memory_usages) / len(memory_usages) if memory_usages else 0
        )

        strace_proc = run_strace(
            process.pid, request_count, csvs_dir_path, log_dir_path, "always"
        )
        run_benchmark(request_count, csvs_dir_path, 6382, "always", save_csv=False)
        strace_proc.send_signal(signal.SIGINT)
        strace_proc.wait()

        if not headers_written:
            csv_filename = os.path.join(csvs_dir_path, f"always_{request_count}.csv")
            if not os.path.exists(csv_filename):
                raise FileNotFoundError(f"Expected CSV file not found: {csv_filename}")
            with open(csv_filename, "r") as input_csv:
                headers = next(csv.reader(input_csv))
                csv_writer = csv.DictWriter(
                    consolidated_csv,
                    fieldnames=headers
                    + [
                        "Fsync Type",
                        "CPU Usage",
                        "Memory Usage",
                        "fdatasync_count",
                        "write_count",
                        "io_uring_enter_count",
                        "write_time",
                        "fdatasync_time",
                        "io_uring_enter_time",
                        "total_time",
                        "total_syscall_count",
                        ],
                )
                csv_writer.writeheader()
                headers_written = True

        consolidate_csv(
            request_count, avg_cpu_usage, avg_memory_usage, csv_writer )

    os.remove(os.path.join(csvs_dir_path, f"always_{request_count}.csv"))
    os.remove(os.path.join(csvs_dir_path, f"always_{request_count}_syscalls.csv"))
    os.remove(os.path.join(csvs_dir_path, f"always_{request_count}_syscalls-times.csv"))


if __name__ == "__main__":
    kill_process_on_port(6382)
    time.sleep(3)
    process = run_server("redis-io_uring", config_path, redis_log_path, 6382)
    r = redis.Redis(host="localhost", port=6382)

    run_all_tasks(r, process, request_count)

    stop_server(process)

    exit(0)
