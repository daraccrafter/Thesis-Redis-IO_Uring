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


def run_benchmark_script(script_path, request_count, fsync=None, only_perf=False):
    command = ["sudo", "python3", script_path, str(request_count)]

    if fsync:
        command.append(fsync)

    if only_perf:
        command.append("only_performance")

    result = subprocess.run(command, stdout=sys.stdout, stderr=sys.stderr)

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


def run_benchmarks(request_count, benchmarks_to_run, fsync="all", only_perf=False):
    benchmark_scripts = find_benchmark_scripts("benchmarks")

    for benchmark_name in benchmarks_to_run:
        script_path = benchmark_scripts.get(benchmark_name)
        if script_path:
            print(f"Running {benchmark_name} benchmark...")
            if benchmark_name == "AOF":
                run_benchmark_script(script_path, request_count, fsync, only_perf)
            else:
                run_benchmark_script(script_path, request_count, None, only_perf)
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
    parser.add_argument(
        "--fsync",
        choices=["always", "everysec", "no", "all"],
        default="all",
        help="Specify the fsync mode for the AOF benchmark.",
    )
    parser.add_argument(
        "--no-strace",
        action="store_true",
        default=False,
        help="Run benchmarks without strace.",
    )
    args = parser.parse_args()

    if args.benchmark:
        benchmarks_to_run = args.benchmark
    else:
        benchmarks_to_run = ["RDB", "AOF", "URING_AOF"]

    subprocess.run(["sudo", "./script-cleanup.sh"], check=True)
    run_benchmarks(args.requests, benchmarks_to_run, args.fsync, args.no_strace)
    print("Benchmark test completed successfully.")
