# benchmark_utils.py
import os
import subprocess
import pandas as pd
import matplotlib.pyplot as plt
import yaml
import math
import psutil

base_csv_dir = "csvs"
base_graphs_dir = "graphs"
base_logs_dir = "logs"


def load_config(config_path):
    with open(config_path, "r") as file:
        config = yaml.safe_load(file)
    return config


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


def create_directories(script_dir,timestamp,server1="redis",server2="redis-io_uring"):
    output_dir_s1 = os.path.join(
        script_dir, "data", base_csv_dir, server1, timestamp
    )
    output_dir_s2 = os.path.join(
        script_dir, "data", base_csv_dir, server2, timestamp
    )
    graphs_dir = os.path.join(script_dir,"data",base_graphs_dir, timestamp)
    logs_dir_s1 = os.path.join(script_dir,"data",base_logs_dir, server1,  timestamp)
    logs_dir_s2 = os.path.join(
        script_dir,"data",base_logs_dir, server2, timestamp
    )
    os.makedirs(output_dir_s1, exist_ok=True)
    os.makedirs(output_dir_s2, exist_ok=True)
    os.makedirs(graphs_dir, exist_ok=True)
    os.makedirs(logs_dir_s1, exist_ok=True)
    os.makedirs(logs_dir_s2, exist_ok=True)
    return (
        output_dir_s1,
        output_dir_s2,
        graphs_dir,
        logs_dir_s1,
        logs_dir_s2,
    )


def run_strace(pid, request_count, syscalls_dir, logs_dir, iteration, persistance=""):
    syscalls_filename = os.path.join(
        syscalls_dir, f"{persistance}_syscalls_{request_count}_run{iteration}.csv"
    )
    syscall_times_filename = os.path.join(
        syscalls_dir, f"{persistance}_syscalls_times_{request_count}_run{iteration}.csv"
    )
    log_filename = os.path.join(
        logs_dir, f"{persistance}_syscall_{request_count}_run{iteration}.txt"
    )
    command = [
        "sudo",
        "./strace-syscalls.sh",
        str(pid),
        syscalls_filename,
        syscall_times_filename,
        log_filename,
    ]
    process = subprocess.Popen(
        command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )
    return process


def run_benchmark(
    request_count, output_dir, port, iteration, persistance="", save_csv=True
):
    csv_filename = os.path.join(
        output_dir, f"{persistance}{request_count}_run{iteration}.csv"
    )
    if save_csv:
        last_arg = "--csv"
    else:
        last_arg = "-q"
    command = [
        "./redis-benchmark",
        "-p",
        str(port),
        "-t",
        "set,lpush",
        "-n",
        str(request_count),
        last_arg,
    ]
    if save_csv:
        with open(csv_filename, "w") as csvfile:
            subprocess.run(command, stdout=csvfile, check=True)
    else:
        subprocess.run(
            command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True
        )


def calc_avg_usages(
    cpu_usages,
    memory_usages,
    output_dir,
    request_count,
    iteration,
    persistance="",
):
    cpu_csv_filename = os.path.join(
        output_dir, f"{persistance}_{request_count}_cpu_usage_run{iteration}.csv"
    )
    memory_csv_filename = os.path.join(
        output_dir, f"{persistance}_{request_count}_memory_usage_run{iteration}.csv"
    )
    avg_cpu_usage = sum(cpu_usages) / len(cpu_usages)
    cpu_data = {"avg_cpu_usage": [avg_cpu_usage]}
    cpu_df = pd.DataFrame(cpu_data)
    cpu_df.to_csv(cpu_csv_filename, index=False)

    avg_memory_usage = sum(memory_usages) / len(memory_usages)
    memory_data = {"avg_mem_usage": [avg_memory_usage]}
    memory_df = pd.DataFrame(memory_data)
    memory_df.to_csv(memory_csv_filename, index=False)
    return avg_cpu_usage, avg_memory_usage


def average_rps_csv_files(output_dir, iterations, filename_pattern, avg_filename):
    files = [
        os.path.join(output_dir, filename_pattern.format(iteration=i))
        for i in range(1, iterations + 1)
    ]
    df_list = [pd.read_csv(file) for file in files]
    df_combined = pd.concat(df_list)
    df_avg = df_combined.groupby("test").mean().reset_index()
    avg_csv_filename = os.path.join(output_dir, avg_filename)
    df_avg.to_csv(avg_csv_filename, index=False)
    return df_avg


def average_load_csv_files(request_count, output_dir, iterations,persistance=""):
    cpu_usages = []
    memory_usages = []
    for i in range(1, iterations + 1):
        cpu_csv_filename = os.path.join(
            output_dir, f"{persistance}_{request_count}_cpu_usage_run{i}.csv"
        )
        memory_csv_filename = os.path.join(
            output_dir, f"{persistance}_{request_count}_memory_usage_run{i}.csv"
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


def average_syscall_times_csv_files(
    output_dir, iterations, filename_pattern, avg_filename
):
    files = [
        os.path.join(output_dir, filename_pattern.format(iteration=i))
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

    df_avg = pd.DataFrame(
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
    avg_csv_filename = os.path.join(output_dir, avg_filename)
    df_avg.to_csv(avg_csv_filename, index=False)
    return df_avg


def average_syscalls_files(output_dir, iterations, filename_pattern, avg_filename):
    files = [
        os.path.join(output_dir, filename_pattern.format(iteration=i))
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
    df_avg_syscalls = pd.DataFrame(
        {
            "syscall": ["fdatasync", "write", "io_uring_enter"],
            "avg_count": [avg_fsync, avg_write, avg_io_uring_enter],
        }
    )

    avg_csv_filename = os.path.join(output_dir, avg_filename)
    df_avg_syscalls.to_csv(avg_csv_filename, index=False)
    return df_avg_syscalls


def plot_syscalls_comparison(
    df_avg_1,
    df_avg_2,
    request_count,
    graphs_dir,
    label_1="Label 1",
    label_2="Label 2",
    bar_1_color="blue",
    bar_2_color="red",
    persistance="",
):
    labels = df_avg_1["syscall"]
    syscalls_1 = df_avg_1["avg_count"]
    syscalls_2 = df_avg_2["avg_count"]
    x = range(len(labels))
    bar_width = 0.35
    plt.figure(figsize=(10, 6))
    bar_positions_1 = [p - bar_width / 2 for p in x]
    bar_positions_2 = [p + bar_width / 2 for p in x]
    plt.bar(
        bar_positions_1,
        syscalls_1,
        width=bar_width,
        label=label_1,
        color=bar_1_color,
    )
    plt.bar(
        bar_positions_2,
        syscalls_2,
        width=bar_width,
        label=label_2,
        color=bar_2_color,
    )
    plt.xlabel("Systemcall", fontsize=12)
    plt.ylabel("Average number of calls", fontsize=12)
    combined_positions = [
        (bar_positions_1[i] + bar_positions_2[i]) / 2 for i in range(len(labels))
    ]
    plt.xticks(ticks=combined_positions, labels=labels, rotation=0)
    plt.legend(loc="upper center", bbox_to_anchor=(0.5, 1.15), ncol=2)
    plt.grid(True, axis="y", linestyle="--", alpha=0.7)
    plt.tight_layout()
    plot_filename = os.path.join(
        graphs_dir, f"{persistance}_{request_count}_syscall_count_comparison.png"
    )
    plt.savefig(plot_filename, bbox_inches="tight")
    plt.close()


def plot_cpu_comparison(
    df_avg_1,
    df_avg_2,
    request_count,
    graphs_dir,
    label_1="Label 1",
    label_2="Label 2",
    bar_1_color="blue",
    bar_2_color="red",
    persistance="",
):
    labels = ["CPU Usage"]
    cpu_1 = [df_avg_1[0]]
    cpu_2 = [df_avg_2[0]]
    x = range(len(labels))
    bar_width = 0.35
    plt.figure(figsize=(4, 6))
    bar_positions_1 = [p - bar_width / 2 for p in x]
    bar_positions_2 = [p + bar_width / 2 for p in x]
    plt.bar(
        bar_positions_1,
        cpu_1,
        width=bar_width,
        label=label_1,
        color=bar_1_color,
    )
    plt.bar(
        bar_positions_2,
        cpu_2,
        width=bar_width,
        label=label_2,
        color=bar_2_color,
    )
    plt.ylabel("Average CPU usage (%)", fontsize=12)

    plt.xticks([])
    plt.legend(loc="upper center", bbox_to_anchor=(0.5, 1.15), ncol=1)
    plt.grid(True, axis="y", linestyle="--", alpha=0.7)
    plt.tight_layout()
    plot_filename = os.path.join(
        graphs_dir, f"{persistance}_{request_count}_cpu_comparison.png"
    )
    plt.savefig(plot_filename, bbox_inches="tight")
    plt.close()


def plot_memory_comparison(
    df_avg_1,
    df_avg_2,
    request_count,
    graphs_dir,
    label_1="Label 1",
    label_2="Label 2",
    bar_1_color="blue",
    bar_2_color="red",
    persistance="",
):
    labels = ["Memory Usage"]
    memory_1 = [df_avg_1[1]]
    memory_2 = [df_avg_2[1]]

    x = range(len(labels))
    bar_width = 0.05

    plt.figure(figsize=(4, 6))

    bar_positions_1 = [p - bar_width / 2 for p in x]
    bar_positions_2 = [p + bar_width / 2 for p in x]
    plt.bar(
        bar_positions_1,
        memory_1,
        width=bar_width,
        label=label_1,
        color=bar_1_color,
    )
    plt.bar(
        bar_positions_2,
        memory_2,
        width=bar_width,
        label=label_2,
        color=bar_2_color,
    )

    plt.xticks([])
    plt.ylabel("Average memory usage (MB)", fontsize=12)

    plt.legend(loc="upper center", bbox_to_anchor=(0.5, 1.15), ncol=1)
    plt.grid(True, axis="y", linestyle="--", alpha=0.7)
    plt.tight_layout()

    plot_filename = os.path.join(
        graphs_dir, f"{persistance}_{request_count}_memory_comparison.png"
    )
    plt.savefig(plot_filename)
    plt.close()


def plot_syscall_times_comparison(
    df_avg_1,
    df_avg_2,
    request_count,
    graphs_dir,
    label_1="Label 1",
    label_2="Label 2",
    bar_1_color="blue",
    bar_2_color="red",
    persistance="",
):
    labels = df_avg_1["syscall"]
    syscalls_1 = df_avg_1["avg_time"]  # Keep in seconds
    syscalls_2 = df_avg_2["avg_time"]  # Keep in seconds
    x = range(len(labels))
    bar_width = 0.35
    plt.figure(figsize=(10, 6))
    bar_positions_1 = [p - bar_width / 2 for p in x]
    bar_positions_2 = [p + bar_width / 2 for p in x]
    plt.bar(
        bar_positions_1,
        syscalls_1,
        width=bar_width,
        label=label_1,
        color=bar_1_color,
    )
    plt.bar(
        bar_positions_2,
        syscalls_2,
        width=bar_width,
        label=label_2,
        color=bar_2_color,
    )
    plt.xlabel("Systemcall", fontsize=12)
    plt.ylabel("Average latency [s]", fontsize=12)
    plt.yscale("log")
    combined_positions = [
        (bar_positions_1[i] + bar_positions_2[i]) / 2 for i in range(len(labels))
    ]
    plt.xticks(ticks=combined_positions, labels=labels, rotation=0)
    plt.legend(loc="upper center", bbox_to_anchor=(0.5, 1.15), ncol=2)
    plt.grid(True, axis="y", linestyle="--", alpha=0.7)
    plt.tight_layout()
    plot_filename = os.path.join(
        graphs_dir, f"{persistance}_{request_count}_syscall_times_comparison.png"
    )
    plt.savefig(plot_filename, bbox_inches="tight")
    plt.close()


def plot_rps_comparison(
    df_avg_1,
    df_avg_2,
    request_count,
    graphs_dir,
    label_1="Label 1",
    label_2="Label 2",
    bar_1_color="blue",
    bar_2_color="red",
):
    labels = df_avg_1["test"]
    rps_1 = df_avg_1["rps"]
    rps_2 = df_avg_2["rps"]
    x = range(len(labels))
    bar_width = 0.35
    plt.figure(figsize=(10, 6))
    bar_positions_1 = [p - bar_width / 2 for p in x]
    bar_positions_2 = [p + bar_width / 2 for p in x]
    plt.bar(
        bar_positions_1,
        rps_1,
        width=bar_width,
        label=label_1,
        color=bar_1_color,
    )
    plt.bar(
        bar_positions_2,
        rps_2,
        width=bar_width,
        label=label_2,
        color=bar_2_color,
    )
    plt.xlabel("Operation", fontsize=12)
    plt.ylabel("Requests per second (RPS)", fontsize=12)
    combined_positions = [
        (bar_positions_1[i] + bar_positions_2[i]) / 2 for i in range(len(labels))
    ]
    plt.xticks(ticks=combined_positions, labels=labels, rotation=0)
    plt.legend(loc="upper center", bbox_to_anchor=(0.5, 1.15), ncol=2)
    plt.grid(True, axis="y", linestyle="--", alpha=0.7)
    plt.tight_layout()
    plot_filename = os.path.join(
        graphs_dir, f"{request_count}_numrequests_rps_comparison.png"
    )
    plt.savefig(plot_filename, bbox_inches="tight")
    plt.close()
