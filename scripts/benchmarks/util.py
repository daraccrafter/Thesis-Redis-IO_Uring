import os
import subprocess
import pandas as pd
import matplotlib.pyplot as plt
import math
import psutil
import signal
import redis
import time
import concurrent.futures

base_csv_dir = "csvs"
base_graphs_dir = "graphs"
base_logs_dir = "logs"


def verify_keys(client, total_keys, csvdir, logsdir):
    chunk_size = total_keys // 100
    futures = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:
        for i in range(0, total_keys, chunk_size):
            future = executor.submit(check_keys_range, client, i + 1, i + chunk_size)
            futures.append(future)

    correct_keys = {}
    incorrect_keys = {}

    for future in concurrent.futures.as_completed(futures):
        chunk_keys = future.result()
        for key, value in chunk_keys.items():
            if value == "Incorrect":
                incorrect_keys[key] = value
            else:
                correct_keys[key] = value

    sorted_correct_keys = dict(
        sorted(correct_keys.items(), key=lambda item: int(item[1]))
    )
    sorted_incorrect_keys = dict(
        sorted(incorrect_keys.items(), key=lambda item: int(item[0].split("_")[1]))
    )

    total = len(correct_keys) + len(incorrect_keys)
    data = {
        "Total": [total],
        "Correct": [len(correct_keys)],
        "Incorrect": [len(incorrect_keys)],
    }

    csvfile = os.path.join(csvdir, "data-integrity.csv")
    pd.DataFrame(data).to_csv(csvfile, index=False)

    logfile = os.path.join(logsdir, "data-integrity.log")
    with open(logfile, "w") as f:
        f.write("Correct Keys:\n")
        for key, value in sorted_correct_keys.items():
            f.write(f"{key}: {value}\n")

        f.write("\nIncorrect Keys:\n")
        for key, value in sorted_incorrect_keys.items():
            f.write(f"{key}: {value}\n")

    return sorted_incorrect_keys, sorted_correct_keys


def check_keys_range(client, start_index, end_index):
    keys = {}

    for i in range(start_index, end_index + 1):
        expected_value = i
        actual_value = client.get(f"key_{i}")

        if actual_value is None or int(actual_value) != expected_value:
            keys[f"key_{i}"] = "Incorrect"
        else:
            keys[f"key_{i}"] = actual_value

    return keys


def find_aof_file_with_increment(currdir):
    appendonlydir_path = os.path.join(currdir, "appendonlydir")
    files = os.listdir(appendonlydir_path)

    for file in files:
        if f".incr." in file:
            return os.path.join(currdir, "appendonlydir", file)

    return None


def check_aof_file(currdir, logdir):
    command = ["./redis-check-aof", find_aof_file_with_increment(currdir)]
    with open(os.path.join(logdir, "redis-aof-check.log"), "w") as f:
        subprocess.run(command, check=True, stdout=f)


def remove_appendonlydir(currdir):
    appendonlydir_path = os.path.join(currdir, "appendonlydir")
    rm_command = f"rm -rf {appendonlydir_path}"
    subprocess.run(rm_command, shell=True, check=True)


def check_redis_connection(port1):
    try:
        r = redis.Redis(port=port1)
        r.ping()

        return True

    except redis.ConnectionError:
        return False

    except Exception as e:
        return False


def run_server(implementation, configpath, logpath, port):
    with open(logpath, "w") as logfile:
        command = [
            "./src/redis-server",
            "redis.conf",
            "--port",
            str(port),
        ]
        process = subprocess.Popen(
            command, stdout=logfile, stderr=logfile, cwd="../" + implementation
        )
    while not check_redis_connection(port):
        time.sleep(0.1)
    return process


def stop_server(process):
    process.send_signal(signal.SIGTERM)
    process.wait()


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


import numpy as np


def measure_idle_cpu_usage(pid, duration=5):
    idle_cpu_usages = []
    end_time = time.time() + duration

    try:
        p = psutil.Process(pid)
        while time.time() < end_time:
            with p.oneshot():
                cpu_percent = p.cpu_percent(
                    interval=1
                )  # Get CPU usage for the specific process
                idle_cpu_usages.append(cpu_percent)
                print(f"Measured idle CPU usage for PID {pid}: {cpu_percent}%")

        average_idle_cpu = np.mean(idle_cpu_usages) if idle_cpu_usages else 0
        print(
            f"Average idle CPU usage for PID {pid} before benchmark: {average_idle_cpu:.2f}%"
        )
        return average_idle_cpu
    except psutil.NoSuchProcess:
        print(f"Process with PID {pid} not found.")
        return 0


def create_directories(
    script_dir, timestamp, server1="redis", server2="redis-io_uring"
):
    output_dir_s1 = os.path.join(script_dir, "data", base_csv_dir, server1, timestamp)
    output_dir_s2 = os.path.join(script_dir, "data", base_csv_dir, server2, timestamp)
    graphs_dir = os.path.join(script_dir, "data", base_graphs_dir, timestamp)
    logs_dir_s1 = os.path.join(script_dir, "data", base_logs_dir, server1, timestamp)
    logs_dir_s2 = os.path.join(script_dir, "data", base_logs_dir, server2, timestamp)
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


def run_strace(pid, request_count, syscalls_dir, logs_dir, name=""):
    if name != "":
        syscalls_filename = os.path.join(syscalls_dir, f"{name}_syscalls.csv")
        syscall_times_filename = os.path.join(syscalls_dir, f"{name}_syscalls_times.csv")
        log_filename = os.path.join(logs_dir, f"{name}_strace.txt")
    else:
        syscalls_filename = os.path.join(syscalls_dir, f"syscalls.csv")
        syscall_times_filename = os.path.join(syscalls_dir, f"syscalls_times.csv")
        log_filename = os.path.join(logs_dir, "strace.txt")
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


def kill_process_on_port(port):
    find_process_command = f"lsof -t -i:{port}"
    try:
        process_ids = (
            subprocess.check_output(find_process_command, shell=True)
            .decode()
            .strip()
            .split("\n")
        )
    except subprocess.CalledProcessError as e:
        if e.returncode == 1:
            return
        else:
            raise

    for pid in process_ids:
        if pid:
            print(f"Killing process {pid} on port {port}")
            kill_command = f"kill -9 {pid}"
            subprocess.run(kill_command, shell=True)
            time.sleep(5)


def run_benchmark(
    request_count, output_dir, port, name="", save_csv=True, typebench=""
):
    if name != "":
        csv_filename = os.path.join(output_dir, f"{name}_performance.csv")
    else:
        csv_filename = os.path.join(output_dir, f"performance.csv")

    if save_csv:
        last_arg = "--csv"
    else:
        last_arg = "-q"

    command = [
        "./redis-benchmark",
        "-p",
        str(port),
        "-c",
        "50",
        "-t",
        "set,lpush,sadd,incr",
        "-n",
        str(request_count // 4),
        last_arg,
    ]

    print(f"Running {typebench} for {request_count} requests")

    if save_csv:
        with open(csv_filename, "w") as csvfile:
            process = subprocess.Popen(command, stdout=csvfile, stderr=subprocess.PIPE)
    else:
        process = subprocess.Popen(
            command, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE
        )

    try:
        while process.poll() is None:
            print("\tBenchmark is still running...")
            time.sleep(20)
    except KeyboardInterrupt:
        process.terminate()
        print("Benchmark was terminated by user.")

    process.wait()

    if process.returncode != 0:
        raise subprocess.CalledProcessError(process.returncode, command)

    print("Benchmark completed successfully.")


def calc_avg_usages(
    cpu_usages,
    memory_usages,
    output_dir,
    request_count,
    iteration,
    name="",
):
    if name != "":
        cpu_csv_filename = os.path.join(
            output_dir, f"{name}_{request_count}_cpu_usage_run{iteration}.csv"
        )
        memory_csv_filename = os.path.join(
            output_dir, f"{name}_{request_count}_memory_usage_run{iteration}.csv"
        )
    else:
        cpu_csv_filename = os.path.join(
            output_dir, f"{request_count}_cpu_usage_run{iteration}.csv"
        )
        memory_csv_filename = os.path.join(
            output_dir, f"{request_count}_memory_usage_run{iteration}.csv"
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
