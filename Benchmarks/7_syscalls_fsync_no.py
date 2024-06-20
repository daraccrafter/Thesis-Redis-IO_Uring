import subprocess
import os
import sys
import pandas as pd
import matplotlib.pyplot as plt
import signal
import math
import time

benchmark = "7_syscalls_fsync_no"
request_counts = [1000, 10000, 100000]

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


syscalls_dir_redis = os.path.join(base_csv_dir, "redis", "7", timestamp)
syscalls_dir_redis_io_uring = os.path.join(
    base_csv_dir, "redis-io_uring", "7", timestamp
)
graphs_dir = os.path.join(base_graphs_dir, "7", timestamp)
logs_redis_dir = os.path.join("logs", "redis", "7", timestamp)
logs_redis_io_uring_dir = os.path.join("logs", "redis-io_uring", "7", timestamp)
os.makedirs(graphs_dir, exist_ok=True)
os.makedirs(syscalls_dir_redis, exist_ok=True)
os.makedirs(syscalls_dir_redis_io_uring, exist_ok=True)
os.makedirs(logs_redis_dir, exist_ok=True)
os.makedirs(logs_redis_io_uring_dir, exist_ok=True)


def run_benchmark(request_count, port, iteration, pid, syscalls_dir, logs_dir):
    syscalls_filename = os.path.join(
        syscalls_dir, f"{request_count}_numrequests_run{iteration}.csv"
    )
    syscall_times_filename = os.path.join(
        syscalls_dir, f"syscall_time_{request_count}_run{iteration}.csv"
    )
    log_filename = os.path.join(logs_dir, f"syscall_{request_count}_run{iteration}.txt")

    command = [
        "./redis-benchmark",
        "-p",
        str(port),
        "-t",
        "set,lpush",
        "-n",
        str(request_count),
    ]
    strace = [
        "sudo",
        "./strace-syscalls.sh",
        str(pid),
        syscalls_filename,
        syscall_times_filename,
        log_filename,
    ]
    strace_process = subprocess.Popen(
        strace, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )
    time.sleep(0.5)
    subprocess.run(
        command, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL, check=True
    )
    time.sleep(0.5)
    strace_process.send_signal(signal.SIGINT)
    strace_process.wait()


def average_syscall_times_files(request_count, syscalls_dir, iterations):
    files = [
        os.path.join(syscalls_dir, f"syscall_time_{request_count}_run{i}.csv")
        for i in range(1, iterations + 1)
    ]

    counts = {"write": [], "fdatasync": [], "io_uring_enter": []}

    for file in files:
        df = pd.read_csv(file)
        counts["write"].append(df[df["syscall"] == "write"]["time"].values[0])
        counts["fdatasync"].append(df[df["syscall"] == "fdatasync"]["time"].values[0])
        counts["io_uring_enter"].append(
            df[df["syscall"] == "io_uring_enter"]["time"].values[0]
        )

    avg_write_time = sum(counts["write"]) / len(counts["write"])
    avg_fdatasync_time = sum(counts["fdatasync"]) / len(counts["fdatasync"])
    avg_io_uring_enter_time = sum(counts["io_uring_enter"]) / len(
        counts["io_uring_enter"]
    )
    total_time = avg_write_time + avg_fdatasync_time + avg_io_uring_enter_time

    avg_syscalls = pd.DataFrame(
        {
            "syscall": ["write", "fdatasync", "io_uring_enter", "total"],
            "avg_time": [
                avg_write_time,
                avg_fdatasync_time,
                avg_io_uring_enter_time,
                total_time,
            ],
        }
    )

    avg_syscalls_filename = os.path.join(
        syscalls_dir, f"{request_count}_numrequests_avg_syscalls_times.csv"
    )
    avg_syscalls.to_csv(avg_syscalls_filename, index=False)

    return avg_syscalls


def average_syscalls_files(request_count, syscalls_dir, iterations):
    files = [
        os.path.join(syscalls_dir, f"{request_count}_numrequests_run{i}.csv")
        for i in range(1, iterations + 1)
    ]
    counts = {"fdatasync": [], "write": [], "io_uring_enter": []}

    for file in files:
        df = pd.read_csv(file)
        counts["fdatasync"].append(df[df["syscall"] == "fdatasync"]["count"].values[0])
        counts["write"].append(df[df["syscall"] == "write"]["count"].values[0])
        counts["io_uring_enter"].append(
            df[df["syscall"] == "io_uring_enter"]["count"].values[0]
        )

    avg_fsync = math.ceil(sum(counts["fdatasync"]) / len(counts["fdatasync"]))
    avg_write = math.ceil(sum(counts["write"]) / len(counts["write"]))
    avg_io_uring_enter = math.ceil(
        sum(counts["io_uring_enter"]) / len(counts["io_uring_enter"])
    )
    avg_syscalls = pd.DataFrame(
        {
            "syscall": ["fdatasync", "write", "io_uring_enter"],
            "avg_count": [avg_fsync, avg_write, avg_io_uring_enter],
        }
    )

    avg_syscalls_filename = os.path.join(
        syscalls_dir, f"{request_count}_numrequests_avg_syscalls.csv"
    )
    avg_syscalls.to_csv(avg_syscalls_filename, index=False)
    return avg_syscalls


def plot_syscalls_comparison(
    avg_syscalls_redis, avg_syscalls_redis_io_uring, request_count
):
    labels = avg_syscalls_redis["syscall"]
    redis_syscalls = avg_syscalls_redis["avg_count"]
    redis_io_uring_syscalls = avg_syscalls_redis_io_uring["avg_count"]

    x = range(len(labels))
    bar_width = 0.35

    plt.figure(figsize=(10, 6))

    bar_positions_redis = [p - bar_width / 2 for p in x]
    bar_positions_io_uring = [p + bar_width / 2 for p in x]

    plt.bar(
        bar_positions_redis,
        redis_syscalls,
        width=bar_width,
        label="Redis",
        color="blue",
    )
    plt.bar(
        bar_positions_io_uring,
        redis_io_uring_syscalls,
        width=bar_width,
        label="Redis io_uring",
        color="red",
    )

    plt.xlabel("Systemcall")
    plt.ylabel("Average number of calls")

    combined_positions = [
        (bar_positions_redis[i] + bar_positions_io_uring[i]) / 2
        for i in range(len(labels))
    ]

    plt.xticks(ticks=combined_positions, labels=labels)

    plt.legend(loc="upper center", bbox_to_anchor=(0.5, 1.15), ncol=2)
    plt.grid(True, axis="y", linestyle="--", alpha=0.7)
    plt.tight_layout()

    plot_filename = os.path.join(
        graphs_dir, f"{request_count}_syscall_count_comparison.png"
    )
    plt.savefig(plot_filename)
    plt.close()


def plot_syscall_times_comparison(
    avg_syscalls_redis, avg_syscalls_redis_io_uring, request_count
):
    labels = avg_syscalls_redis["syscall"]
    redis_syscalls = avg_syscalls_redis["avg_time"]  # Keep in seconds
    redis_io_uring_syscalls = avg_syscalls_redis_io_uring["avg_time"]  # Keep in seconds

    x = range(len(labels))
    bar_width = 0.35  # Adjusted bar width to fit both bars closer together

    plt.figure(figsize=(10, 6))

    bar_positions_redis = [p - bar_width / 2 for p in x]
    bar_positions_io_uring = [p + bar_width / 2 for p in x]

    plt.bar(
        bar_positions_redis,
        redis_syscalls,
        width=bar_width,
        label="Redis",
        color="blue",
    )
    plt.bar(
        bar_positions_io_uring,
        redis_io_uring_syscalls,
        width=bar_width,
        label="Redis io_uring",
        color="red",
    )

    plt.xlabel("Systemcall")
    plt.ylabel("Average latency [s]")
    plt.yscale("log")
    combined_positions = [
        (bar_positions_redis[i] + bar_positions_io_uring[i]) / 2
        for i in range(len(labels))
    ]

    plt.xticks(ticks=combined_positions, labels=labels)

    plt.legend(loc="upper center", bbox_to_anchor=(0.5, 1.15), ncol=2)
    plt.grid(True, axis="y", linestyle="--", alpha=0.7)
    plt.tight_layout()

    plot_filename = os.path.join(
        graphs_dir, f"{request_count}_syscall_times_comparison.png"
    )
    plt.savefig(plot_filename)
    plt.close()


if __name__ == "__main__":
    for i in range(1, iterations + 1):
        print(f"\tIteration {i}:")
        for count in request_counts:
            print(f"\t\tRunning benchmark with {count} requests on Redis io_uring...")
            run_benchmark(
                count,
                6379,
                i,
                pid_redis_io_uring,
                syscalls_dir_redis_io_uring,
                logs_redis_io_uring_dir,
            )
        for count in request_counts:
            print(f"\t\tRunning benchmark with {count} requests on Redis...")
            run_benchmark(count, 6380, i, pid_redis, syscalls_dir_redis, logs_redis_dir)

    for count in request_counts:
        avg_syscalls_redis = average_syscalls_files(
            count, syscalls_dir_redis, iterations
        )
        avg_syscalls_redis_io_uring = average_syscalls_files(
            count, syscalls_dir_redis_io_uring, iterations
        )
        avg_syscalls_times_redis = average_syscall_times_files(
            count, syscalls_dir_redis, iterations
        )
        avg_syscalls_times_redis_io_uring = average_syscall_times_files(
            count, syscalls_dir_redis_io_uring, iterations
        )
        plot_syscalls_comparison(avg_syscalls_redis, avg_syscalls_redis_io_uring, count)
        plot_syscall_times_comparison(
            avg_syscalls_times_redis, avg_syscalls_times_redis_io_uring, count
        )

    exit(0)
