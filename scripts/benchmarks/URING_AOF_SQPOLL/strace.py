import sys
import os
import redis
import time
import signal

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.benchmarks.util import (
    run_server,
    stop_server,
    run_benchmark,
    kill_process_on_port,
    run_strace,
    average_syscall_times_csv_files,
    average_syscalls_files,
)

appendfsync_configs = ["always", "everysec", "no"]
currdir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(currdir, "redis.conf")
log_dir_path = os.path.join(currdir, "logs")
redis_log_path = os.path.join(log_dir_path, "redis.log")
csvs_dir_path = os.path.join(currdir, "csvs")
os.makedirs(csvs_dir_path, exist_ok=True)
os.makedirs(log_dir_path, exist_ok=True)
tempdir = os.path.join(currdir, "temp")
os.makedirs(tempdir, exist_ok=True)

if len(sys.argv) != 3:
    print("Arg error")
    exit(1)

iterations = int(sys.argv[1])
request_counts = list(map(int, sys.argv[2].split(",")))

if __name__ == "__main__":
    kill_process_on_port(6384)
    process = run_server("redis-io_uring", config_path, redis_log_path, 6384)
    r = redis.Redis(host="localhost", port=6384)
    print("\tStrace")
    for i in range(1, iterations + 1):
        for fsync in appendfsync_configs:
            r.config_set("appendfsync", fsync)
            for count in request_counts:
                strace_proc = run_strace(
                    process.pid, count, csvs_dir_path, log_dir_path, i, fsync
                )
                run_benchmark(count, csvs_dir_path, 6384, i, fsync, False)
                strace_proc.send_signal(signal.SIGINT)
                strace_proc.wait()

    for count in request_counts:
        for fsync in appendfsync_configs:
            filename_pattern_syscalls = f"{fsync}_{count}_syscalls_run{{iteration}}.csv"
            filename_pattern_syscall_times = (
                f"{fsync}_{count}_syscalls-times_run{{iteration}}.csv"
            )
            average_syscalls_files(
                csvs_dir_path,
                iterations,
                filename_pattern_syscalls,
                f"{fsync}_{count}_syscalls_avg.csv",
            )
            average_syscall_times_csv_files(
                csvs_dir_path,
                iterations,
                filename_pattern_syscall_times,
                f"{fsync}_{count}_syscalls-times_avg.csv",
            )
    stop_server(process)

    exit(0)
