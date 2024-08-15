import sys
import os
import redis
import csv
import threading
import signal
import time
from datetime import datetime

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

if len(sys.argv) < 2:
    print("Usage: script.py <request_count> [only_performance]")
    exit(1)

request_count = int(sys.argv[1])
only_performance = len(sys.argv) > 2 and sys.argv[2].lower() == "only_performance"

timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
run_data_dir = os.path.join(currdir, "data", f"RDB-{timestamp}")
os.makedirs(run_data_dir, exist_ok=True)

time_csv_path = os.path.join(csvs_dir_path, "timing_log.csv")
with open(time_csv_path, "w", newline="") as time_csv:
    fieldnames = ["Benchmark", "Time (seconds)"]
    writer = csv.DictWriter(time_csv, fieldnames=fieldnames)
    writer.writeheader()


def log_time(benchmark_name, duration):
    with open(time_csv_path, "a", newline="") as time_csv:
        writer = csv.DictWriter(time_csv, fieldnames=["Benchmark", "Time (seconds)"])
        writer.writerow({"Benchmark": benchmark_name, "Time (seconds)": duration})


def run_all_tasks(r, process, request_count):
    r.config_set("appendonly", "no")
    total_start_time = time.time()
    start_time = time.time()
    run_benchmark(
        request_count,
        csvs_dir_path,
        6381,
        "",
        save_csv=True,
        typebench="performance",
    )
    end_time = time.time()
    log_time("Performance benchmark", end_time - start_time)

    start_time = time.time()
    cpu_usages, memory_usages = [], []
    stop_event = threading.Event()
    monitor_thread = threading.Thread(
        target=monitor_process,
        args=(process.pid, stop_event, cpu_usages, memory_usages),
    )
    monitor_thread.start()
    run_benchmark(
        request_count,
        csvs_dir_path,
        6381,
        "",
        save_csv=False,
        typebench="resource usage",
    )
    stop_event.set()
    monitor_thread.join()
    end_time = time.time()
    log_time("Resource usage benchmark", end_time - start_time)

    avg_cpu_usage = sum(cpu_usages) / len(cpu_usages) if cpu_usages else 0
    avg_memory_usage = sum(memory_usages) / len(memory_usages) if memory_usages else 0

    usage_csv_path = os.path.join(csvs_dir_path, f"usage.csv")
    with open(usage_csv_path, "w", newline="") as usage_csv:
            fieldnames = [
            "Metric",
            "Average",
            ]
            writer = csv.DictWriter(usage_csv, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerow(
                {
                "Metric": "CPU Usage (%)",
                "Average": avg_cpu_usage,
                }
            )
            writer.writerow(
                {
                "Metric": "Memory Usage (MB)",
                "Average": avg_memory_usage,
                }
            )
    if only_performance:
        total_end_time = time.time()
        log_time("Total", total_end_time - total_start_time)
        return

    start_time = time.time()
    strace_proc = run_strace(
        process.pid, request_count, csvs_dir_path, log_dir_path, ""
    )
    run_benchmark(
        request_count, csvs_dir_path, 6381, "", save_csv=False, typebench="strace"
    )
    strace_proc.send_signal(signal.SIGINT)
    strace_proc.wait()
    end_time = time.time()
    log_time("Strace benchmark", end_time - start_time)

    total_end_time = time.time()
    log_time("Total", total_end_time - total_start_time)


def move_files_to_data_dir():
    os.makedirs(run_data_dir, exist_ok=True)
    os.system(f"mv {csvs_dir_path}/*.csv {run_data_dir}")
    os.system(f"mv {log_dir_path}/*.log {run_data_dir}")


if __name__ == "__main__":
    kill_process_on_port(6381)
    os.system(f"rm -rf {csvs_dir_path}/*.csv")
    os.system(f"rm -rf {log_dir_path}/*.log")
    process = run_server("redis", config_path, redis_log_path, 6381)
    r = redis.Redis(host="localhost", port=6381)

    run_all_tasks(r, process, request_count)

    stop_server(process)

    move_files_to_data_dir()

    exit(0)