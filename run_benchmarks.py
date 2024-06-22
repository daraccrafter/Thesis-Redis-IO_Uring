import os
import subprocess
import sys
import signal
import time
import argparse
from datetime import datetime

benchmark_scripts_dir = "Benchmarks"

redis_server_process = None
redis_io_uring_server_process = None
redis_rdb_server_command = [
    "./src/redis-server",
]


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
    if redis_server_process:
        stop_redis_server(redis_server_process)
    if redis_io_uring_server_process:
        stop_redis_server(redis_io_uring_server_process)
    if result:
        result.send_signal(signal.SIGTERM)
        result.wait()
    sys.exit(0)


def run_benchmark_script(script, timestamp, iterations):
    global redis_server_process, redis_io_uring_server_process, result

    remove_appendonly = [
        "rm",
        "-rf",
        "redis/appendonlydir",
        "redis-io_uring/appendonlydir",
    ]
    subprocess.run(remove_appendonly, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    benchmark_number = script.split("_")[0]
    redis_server_command = [
        "./src/redis-server",
        f"../Configs/redis/{benchmark_number}_redis.conf",
    ]
    redis_io_uring_server_command = [
        "./src/redis-server",
        f"../Configs/redis-io_uring/{benchmark_number}_redis.conf",
    ]

    redis_server_process = start_redis_server(redis_server_command, cwd="redis")
    if benchmark_number == "0" or benchmark_number == "10":
        redis_rdb_server_process = start_redis_server(
            redis_rdb_server_command, cwd="redis"
        )
    else:
        redis_io_uring_server_process = start_redis_server(
            redis_io_uring_server_command, cwd="redis-io_uring"
        )
    time.sleep(3)

    script_path = os.path.join(benchmark_scripts_dir, script)
    print(
        f"Running {script_path} with timestamp {timestamp} for {iterations} iterations..."
    )
    if benchmark_number == "0" or benchmark_number == "10":
        result = subprocess.run(
            [
                "python3",
                script_path,
                timestamp,
                str(iterations),
                str(redis_server_process.pid),
                str(redis_rdb_server_process.pid),
            ],
            stdout=sys.stdout,
            stderr=sys.stderr,
        )
    else:
        result = subprocess.run(
            [
                "python3",
                script_path,
                timestamp,
                str(iterations),
                str(redis_server_process.pid),
                str(redis_io_uring_server_process.pid),
            ],
            stdout=sys.stdout,
            stderr=sys.stderr,
        )

    stop_redis_server(redis_server_process)
    if benchmark_number == "0" or benchmark_number == "10":
        stop_redis_server(redis_rdb_server_process)
    else:
        stop_redis_server(redis_io_uring_server_process)
    if result.returncode != 0:
        print(f"{script_path} failed with return code {result.returncode}")
        sys.exit(1)


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


def main():
    try:
        parser = argparse.ArgumentParser(description="Run benchmark scripts.")
        parser.add_argument("scripts", nargs="*", help="The benchmark scripts to run")
        parser.add_argument(
            "--iterations",
            type=int,
            default=1,
            help="Number of times to run each benchmark script",
        )
        args = parser.parse_args()

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

        if args.scripts:
            for script in args.scripts:
                if script.startswith("Benchmarks/"):
                    script = os.path.relpath(script, benchmark_scripts_dir)
                script_name = os.path.basename(script)
                run_benchmark_script(script_name, timestamp, args.iterations)
        else:
            benchmark_scripts = [
                f for f in os.listdir(benchmark_scripts_dir) if f.endswith(".py")
            ]
            benchmark_scripts.sort() 
            for script in benchmark_scripts:
                run_benchmark_script(script, timestamp, args.iterations)
    finally:
        print("All benchmark tests completed successfully.")
        sys.exit(0)


if __name__ == "__main__":
    main()
