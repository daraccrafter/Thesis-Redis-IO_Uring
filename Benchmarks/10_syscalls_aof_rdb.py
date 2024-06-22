import subprocess
import os
import sys
import pandas as pd
import matplotlib.pyplot as plt
import signal
import math
import time

benchmark = "10_syscalls_aof_rdb"
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
pid_redis_rdb = int(sys.argv[4])


syscalls_dir_redis = os.path.join(base_csv_dir, "redis", "10", timestamp)
graphs_dir = os.path.join(base_graphs_dir, "10", timestamp)
logs_redis_dir = os.path.join("logs", "redis", "10", timestamp)
os.makedirs(graphs_dir, exist_ok=True)
os.makedirs(syscalls_dir_redis, exist_ok=True)
os.makedirs(logs_redis_dir, exist_ok=True)


def run_benchmark(
    request_count, port, iteration, pid, syscalls_dir, logs_dir, persistance
):
    syscalls_filename = os.path.join(
        syscalls_dir, f"syscall_{persistance}_{request_count}_run{iteration}.csv"
    )
    syscall_times_filename = os.path.join(
        syscalls_dir, f"syscall_time_{persistance}_{request_count}_run{iteration}.csv"
    )
    log_filename = os.path.join(
        logs_dir, f"syscall_{persistance}_{request_count}_run{iteration}.txt"
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


def average_syscall_times_files(request_count, syscalls_dir, iterations, persistance):
    files = [
        os.path.join(
            syscalls_dir, f"syscall_time_{persistance}_{request_count}_run{i}.csv"
        )
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
        syscalls_dir, f"avg_syscall_times_{persistance}_{request_count}.csv"
    )
    avg_syscalls.to_csv(avg_syscalls_filename, index=False)

    return avg_syscalls


def average_syscalls_files(request_count, syscalls_dir, iterations, persistance):
    files = [
        os.path.join(syscalls_dir, f"syscall_{persistance}_{request_count}_run{i}.csv")
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
        syscalls_dir, f"avg_syscall_{persistance}_{request_count}.csv"
    )
    avg_syscalls.to_csv(avg_syscalls_filename, index=False)
    return avg_syscalls


def plot_syscalls_comparison(
    avg_syscalls_redis_aof, avg_syscalls_redis_rdb, request_count
):
    labels = avg_syscalls_redis_aof["syscall"]
    redis_aof_syscalls = avg_syscalls_redis_aof["avg_count"]
    redis_rdb_syscalls = avg_syscalls_redis_rdb["avg_count"]

    x = range(len(labels))
    bar_width = 0.35

    plt.figure(figsize=(10, 6))

    bar_positions_redis_rdb = [p - bar_width / 2 for p in x]
    bar_positions_redis_aof = [p + bar_width / 2 for p in x]
    plt.bar(
        bar_positions_redis_rdb,
        redis_rdb_syscalls,
        width=bar_width,
        label="Redis RDB",
        color="green",
    )
    plt.bar(
        bar_positions_redis_aof,
        redis_aof_syscalls,
        width=bar_width,
        label="Redis AOF (appendfsync = always)",
        color="blue",
    )

    plt.xlabel("Systemcall", fontsize=12)
    plt.ylabel("Average number of calls", fontsize=12)

    combined_positions = [
        (bar_positions_redis_aof[i] + bar_positions_redis_rdb[i]) / 2
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
    avg_syscalls_redis_aof, avg_syscalls_rdb, request_count
):
    labels = avg_syscalls_redis_aof["syscall"]
    redis_aof_syscalls = avg_syscalls_redis_aof["avg_time"]
    redis_rdb_syscalls = avg_syscalls_rdb["avg_time"]

    x = range(len(labels))
    bar_width = 0.35

    plt.figure(figsize=(10, 6))

    bar_positions_redis_rdb = [p - bar_width / 2 for p in x]
    bar_positions_redis_aof = [p + bar_width / 2 for p in x]

    plt.bar(
        bar_positions_redis_rdb,
        redis_rdb_syscalls,
        width=bar_width,
        label="Redis RDB",
        color="green",
    )
    plt.bar(
        bar_positions_redis_aof,
        redis_aof_syscalls,
        width=bar_width,
        label="Redis AOF (appendfsync = always)",
        color="blue",
    )

    plt.xlabel("Systemcall", fontsize=12)
    plt.ylabel("Average latency [s]", fontsize=12)
    plt.yscale("log")
    combined_positions = [
        (bar_positions_redis_aof[i] + bar_positions_redis_rdb[i]) / 2
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
            print(f"\t\tRunning benchmark with {count} requests on Redis RDB...")
            run_benchmark(
                count, 6379, i, pid_redis_rdb, syscalls_dir_redis, logs_redis_dir, "rdb"
            )
        for count in request_counts:
            print(f"\t\tRunning benchmark with {count} requests on Redis AOF...")
            run_benchmark(
                count, 6380, i, pid_redis, syscalls_dir_redis, logs_redis_dir, "aof"
            )

    for count in request_counts:
        avg_syscalls_redis_aof = average_syscalls_files(
            count, syscalls_dir_redis, iterations, "aof"
        )
        avg_syscalls_redis_rdb = average_syscalls_files(
            count, syscalls_dir_redis, iterations, "rdb"
        )
        avg_syscalls_times_redis_aof = average_syscall_times_files(
            count, syscalls_dir_redis, iterations, "aof"
        )
        avg_syscalls_times_redis_rdb = average_syscall_times_files(
            count, syscalls_dir_redis, iterations, "rdb"
        )
        plot_syscalls_comparison(avg_syscalls_redis_aof, avg_syscalls_redis_rdb, count)
        plot_syscall_times_comparison(
            avg_syscalls_times_redis_aof, avg_syscalls_times_redis_rdb, count
        )

    exit(0)
