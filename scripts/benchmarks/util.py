import os
import subprocess
import pandas as pd
import math
import psutil
import signal
import redis
import time

base_csv_dir = "csvs"
base_graphs_dir = "graphs"
base_logs_dir = "logs"

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
        


def run_strace(pid, request_count, syscalls_dir, logs_dir, name=""):
    if name != "":
        syscalls_filename = os.path.join(syscalls_dir, f"{name}_syscalls.csv")
        syscall_times_filename = os.path.join(
            syscalls_dir, f"{name}_syscalls_times.csv"
        )
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
        "set,hset,incr,lpush",
        "-n",
        str(request_count//4),
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
