import os
import subprocess
import sys
import signal
import argparse


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


def run_benchmark_script(script_path, request_count):
    result = subprocess.run(
        ["sudo", "python3", script_path, str(request_count)],
        stdout=sys.stdout,
        stderr=sys.stderr,
    )

    if result.returncode != 0:
        print(
            f"{os.path.basename(script_path)} failed with return code {result.returncode}"
        )
        sys.exit(1)


def find_benchmark_scripts(path):
    benchmark_scripts = {}
    for root, dirs, files in os.walk(path):
        for dir_name in dirs:
            if dir_name in ["AOF", "RDB", "URING_AOF"]:
                dir_path = os.path.join(root, dir_name)
                for file in os.listdir(dir_path):
                    if file == "benchmark.py":
                        benchmark_scripts[dir_name] = os.path.join(dir_path, file)
    return benchmark_scripts


def run_benchmarks(request_count, benchmarks_to_run):
    benchmark_scripts = find_benchmark_scripts("benchmarks")

    for benchmark_name in benchmarks_to_run:
        script_path = benchmark_scripts.get(benchmark_name)
        if script_path:
            print(f"Running {benchmark_name} benchmark...")
            run_benchmark_script(script_path, request_count)
        else:
            print(f"No benchmark script found for {benchmark_name}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run specific benchmark scripts.")
    parser.add_argument(
        "--benchmark",
        choices=["AOF", "RDB", "URING_AOF"],
        nargs="*", 
        help="Specify which benchmark to run: AOF, RDB, or URING_AOF. If not specified, runs all benchmarks.",
    )
    parser.add_argument(
        "--requests", type=int, default=100000, help="Request count for the benchmark."
    )
    args = parser.parse_args()

    if args.benchmark:
        benchmarks_to_run = args.benchmark
    else:
        benchmarks_to_run = ["AOF", "RDB", "URING_AOF"]

    subprocess.run(["sudo", "./clean-redis-persist.sh"], check=True) 
    run_benchmarks(args.requests, benchmarks_to_run)
    print("Benchmark test completed successfully.")
