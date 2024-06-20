import subprocess
import os
import sys
import pandas as pd
import matplotlib.pyplot as plt
import psutil
import time
import threading

benchmark = "1_requests_fsync_always"
request_counts = [1000000]

base_csv_dir = "csvs"
base_graphs_dir = "graphs"

if len(sys.argv) != 5:
    print(
        "Usage: {benchmark}.py <timestamp> <iterations> <pid_redis> <pid_redis_io_uring>"
    )
    exit(1)

timestamp = sys.argv[1]
iterations = int(sys.argv[2])
pid_redis = int(sys.argv[3])
pid_redis_io_uring = int(sys.argv[4])

output_dir_redis = os.path.join(base_csv_dir, "redis", "9", timestamp)
output_dir_redis_io_uring = os.path.join(base_csv_dir, "redis-io_uring", "9", timestamp)
graphs_dir = os.path.join(base_graphs_dir, "9", timestamp)
os.makedirs(output_dir_redis, exist_ok=True)
os.makedirs(output_dir_redis_io_uring, exist_ok=True)
os.makedirs(graphs_dir, exist_ok=True)


def monitor_process(pid, stop_event, cpu_usages, memory_usages):
    try:
        p = psutil.Process(pid)
        while not stop_event.is_set():
            with p.oneshot():
                cpu_percent = p.cpu_percent(None)
                memory_info = p.memory_info().rss / (1024 * 1024)  # in MB
                cpu_usages.append(cpu_percent)
                memory_usages.append(memory_info)
    except psutil.NoSuchProcess:
        print(f"Process {pid} not found")


def run_benchmark(request_count, output_dir, port, iteration, pid):
    cpu_csv_filename = os.path.join(
        output_dir, f"{request_count}_cpu_usage_run{iteration}.csv"
    )
    memory_csv_filename = os.path.join(
        output_dir, f"{request_count}_memory_usage_run{iteration}.csv"
    )
    command = [
        "./redis-benchmark",
        "-p",
        str(port),
        "-t",
        "set,lpush",
        "-n",
        str(request_count),
    ]

    stop_event = threading.Event()
    cpu_usages, memory_usages = [], []
    monitor_thread = threading.Thread(
        target=monitor_process, args=(pid, stop_event, cpu_usages, memory_usages)
    )
    monitor_thread.start()

    subprocess.run(
        command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True
    )

    stop_event.set()
    monitor_thread.join()

    avg_cpu_usage = sum(cpu_usages) / len(cpu_usages)
    cpu_data = {
        "avg_cpu_usage": [avg_cpu_usage],
    }
    cpu_df = pd.DataFrame(cpu_data)
    cpu_df.to_csv(cpu_csv_filename, index=False)

    avg_memory_usage = sum(memory_usages) / len(memory_usages)
    memory_data = {
        "avg_mem_usage": [avg_memory_usage],
    }
    memory_df = pd.DataFrame(memory_data)
    memory_df.to_csv(memory_csv_filename, index=False)


if __name__ == "__main__":
    for i in range(1, iterations + 1):
        print(f"\tIteration {i}:")
        for count in request_counts:
            print(f"\t\tRunning benchmark with {count} requests on Redis io_uring...")
            run_benchmark(count, output_dir_redis_io_uring, 6379, i, pid_redis_io_uring)
        for count in request_counts:
            print(f"\t\tRunning benchmark with {count} requests on Redis...")
            run_benchmark(count, output_dir_redis, 6380, i, pid_redis)

    # for count in request_counts:
    #     avg_redis = average_csv_files(count, output_dir_redis, iterations)
    #     avg_redis_io_uring = average_csv_files(
    #         count, output_dir_redis_io_uring, iterations
    #     )

    #     plot_rps_comparison(avg_redis, avg_redis_io_uring, count)

    exit(0)
