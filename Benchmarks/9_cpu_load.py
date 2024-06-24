import os
import sys
import pandas as pd
import matplotlib.pyplot as plt
import psutil
import threading
import subprocess

benchmark = "9_cpu_load_fsync_always"
request_counts = [100]

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
    cpu_data = {"avg_cpu_usage": [avg_cpu_usage]}
    cpu_df = pd.DataFrame(cpu_data)
    cpu_df.to_csv(cpu_csv_filename, index=False)

    avg_memory_usage = sum(memory_usages) / len(memory_usages)
    memory_data = {"avg_mem_usage": [avg_memory_usage]}
    memory_df = pd.DataFrame(memory_data)
    memory_df.to_csv(memory_csv_filename, index=False)


def average_csv_files(request_count, output_dir, iterations):
    cpu_usages = []
    memory_usages = []
    for i in range(1, iterations + 1):
        cpu_csv_filename = os.path.join(
            output_dir, f"{request_count}_cpu_usage_run{i}.csv"
        )
        memory_csv_filename = os.path.join(
            output_dir, f"{request_count}_memory_usage_run{i}.csv"
        )

        if os.path.exists(cpu_csv_filename):
            cpu_df = pd.read_csv(cpu_csv_filename)
            cpu_usages.append(cpu_df["avg_cpu_usage"].mean())

        if os.path.exists(memory_csv_filename):
            memory_df = pd.read_csv(memory_csv_filename)
            memory_usages.append(memory_df["avg_mem_usage"].mean())

    avg_cpu_usage = sum(cpu_usages) / len(cpu_usages)
    avg_memory_usage = sum(memory_usages) / len(memory_usages)

    avg_csv_filename = os.path.join(output_dir, f"{request_count}_avg_usage.csv")
    avg_data = {"avg_cpu_usage": [avg_cpu_usage], "avg_mem_usage": [avg_memory_usage]}
    avg_df = pd.DataFrame(avg_data)
    avg_df.to_csv(avg_csv_filename, index=False)

    return avg_cpu_usage, avg_memory_usage


def plot_cpu_comparison(avg_redis, avg_redis_io_uring, request_count):
    labels = ["CPU Usage"]
    redis_values = [avg_redis[0]]
    redis_io_uring_values = [avg_redis_io_uring[0]]

    x = range(len(labels))
    bar_width = 0.05

    plt.figure(figsize=(6, 6))

    bar_positions_redis = [p - bar_width / 2 for p in x]
    bar_positions_io_uring = [p + bar_width / 2 for p in x]

    plt.bar(
        bar_positions_redis,
        redis_values,
        width=bar_width,
        label="Redis AOF (appendfsync = always)",
        color="blue",
    )
    plt.bar(
        bar_positions_io_uring,
        redis_io_uring_values,
        width=bar_width,
        label="Redis IO_Uring (appendfsync = always)",
        color="red",
    )

    plt.ylabel("Average CPU usage (%)",fontsize=12)
    plt.xticks([])

    plt.legend(loc="upper center", bbox_to_anchor=(0.5, 1.15), ncol=2)
    plt.grid(True, axis="y", linestyle="--", alpha=0.7)
    plt.tight_layout()

    plot_filename = os.path.join(graphs_dir, f"{request_count}_cpu_comparison.png")
    plt.savefig(plot_filename)
    plt.close()


def plot_memory_comparison(avg_redis, avg_redis_io_uring, request_count):
    labels = ["Memory Usage"]
    redis_values = [avg_redis[1]]
    redis_io_uring_values = [avg_redis_io_uring[1]]

    x = range(len(labels))
    bar_width = 0.05

    plt.figure(figsize=(10, 6))

    bar_positions_redis = [p - bar_width / 2 for p in x]
    bar_positions_io_uring = [p + bar_width / 2 for p in x]
    plt.bar(
        bar_positions_redis,
        redis_values,
        width=bar_width,
        label="Redis AOF (appendfsync = always)",
        color="blue",
    )
    plt.bar(
        bar_positions_io_uring,
        redis_io_uring_values,
        width=bar_width,
        label="Redis IO_Uring (appendfsync = always)",
        color="red",
    )

    plt.xticks([])
    plt.ylabel("Average memory usage (MB)", fontsize=12)

    plt.legend(loc="upper center", bbox_to_anchor=(0.5, 1.15), ncol=2)
    plt.grid(True, axis="y", linestyle="--", alpha=0.7)
    plt.tight_layout()

    plot_filename = os.path.join(graphs_dir, f"{request_count}_memory_comparison.png")
    plt.savefig(plot_filename)
    plt.close()


if __name__ == "__main__":
    for i in range(1, iterations + 1):
        print(f"\tIteration {i}:")
        for count in request_counts:
            print(f"\t\tRunning benchmark with {count} requests on Redis io_uring...")
            run_benchmark(count, output_dir_redis_io_uring, 6379, i, pid_redis_io_uring)
        for count in request_counts:
            print(f"\t\tRunning benchmark with {count} requests on Redis...")
            run_benchmark(count, output_dir_redis, 6380, i, pid_redis)

    for count in request_counts:
        avg_redis = average_csv_files(count, output_dir_redis, iterations)
        avg_redis_io_uring = average_csv_files(
            count, output_dir_redis_io_uring, iterations
        )

        plot_cpu_comparison(avg_redis, avg_redis_io_uring, count)
        plot_memory_comparison(avg_redis, avg_redis_io_uring, count)

    exit(0)
