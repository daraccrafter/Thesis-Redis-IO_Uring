import os
import subprocess
import sys
import signal
import argparse
from datetime import datetime
from benchmarks.benchmark_util import load_config

redis_server_1 = None
redis_io_uring_server_process = None
request_counts = [10000]


def start_redis_server(command, cwd):
    process = subprocess.Popen(
        command, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )
    for line in iter(process.stdout.readline, ""):
        if "Ready to accept connections" in line:
            break
    return process


def stop_redis_server(process):
    if process:
        process.send_signal(signal.SIGTERM)
        process.wait()


def signal_handler(sig, frame):
    print("Interrupt received, shutting down servers...")
    if redis_server_1:
        stop_redis_server(redis_server_1)
    if redis_io_uring_server_process:
        stop_redis_server(redis_io_uring_server_process)
    if result:
        result.send_signal(signal.SIGTERM)
        result.wait()
    sys.exit(0)


def run_benchmark_script(script_path, timestamp, iterations):
    global redis_server_1, redis_io_uring_server_process, result

    script_dir = os.path.dirname(script_path)
    config_path = os.path.join(script_dir, "config.yaml")
    config = load_config(config_path)

    server1 = config["server1"]
    server2 = config["server2"]
    server1_config = config["server1_config"]
    server2_config = config["server2_config"]

    print("Running benchmark script: %s" % script_path)
    server1_conf_path = os.path.join(script_dir, server1_config)
    server2_conf_path = os.path.join(script_dir, server2_config)

    redis_server_1_command = ["./src/redis-server", "../" + str(server1_conf_path)]
    redis_server_2_command = ["./src/redis-server", "../" + str(server2_conf_path)]

    remove_appendonly = [
        "rm",
        "-rf",
        "redis/appendonlydir",
        "redis-io_uring/appendonlydir",
    ]
    subprocess.run(remove_appendonly, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    redis_server_1 = start_redis_server(redis_server_1_command, cwd=server1)
    redis_server_2 = start_redis_server(redis_server_2_command, cwd=server2)

    print(
        f"Running {script_path} with timestamp {timestamp} for {iterations} iterations..."
    )
    result = subprocess.run(
        [
            "sudo",
            "python3",
            script_path,
            timestamp,
            str(iterations),
            str(redis_server_1.pid),
            str(redis_server_2.pid),
            ",".join(map(str, request_counts)),
        ],
        stdout=sys.stdout,
        stderr=sys.stderr,
    )

    stop_redis_server(redis_server_1)
    stop_redis_server(redis_server_2)

    if result.returncode != 0:
        print(f"{script_path} failed with return code {result.returncode}")
        sys.exit(1)


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


def find_benchmark_scripts(path):
    benchmark_scripts = []
    if os.path.isfile(path) and path.endswith(".py"):
        benchmark_scripts.append(path)
    elif os.path.isdir(path):
        for root, _, files in os.walk(path):
            for file in files:
                if file.endswith(".py"):
                    benchmark_scripts.append(os.path.join(root, file))
    return benchmark_scripts


def main():
    try:
        parser = argparse.ArgumentParser(description="Run benchmark scripts.")
        parser.add_argument(
            "paths", nargs="*", help="Paths to benchmark scripts or directories"
        )
        parser.add_argument(
            "--iterations",
            type=int,
            default=1,
            help="Number of times to run each benchmark script",
        )

        args = parser.parse_args()

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

        if not args.paths:
            benchmark_scripts = find_benchmark_scripts("benchmarks")
        else:
            benchmark_scripts = []
            for path in args.paths:
                benchmark_scripts.extend(find_benchmark_scripts(path))

        benchmark_scripts.sort()

        for script in benchmark_scripts:
            run_benchmark_script(script, timestamp, args.iterations)
    finally:
        print("All benchmark tests completed successfully.")
        sys.exit(0)


if __name__ == "__main__":
    main()
