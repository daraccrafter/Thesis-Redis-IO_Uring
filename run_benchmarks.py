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


def run_benchmark_script(script_path, iterations, request_counts):

    result = subprocess.run(
        [
            "sudo",
            "python3",
            script_path,
            str(iterations),
            ",".join(map(str, request_counts)),
        ],
        stdout=sys.stdout,
        stderr=sys.stderr,
    )

    if result.returncode != 0:
        print(
            f"{os.path.basename(script_path)} failed with return code {result.returncode}"
        )
        sys.exit(1)


def plot_comparisons(graphs_dir, request_counts, dirnames):
    os.makedirs(graphs_dir, exist_ok=True)
    comparisons = [
        ("RDB", "URING_AOF", "always"),
        ("AOF", "URING_AOF", "always"),
        ("URING_AOF_SQPOLL", "URING_AOF", "always"),
        ("AOF", "URING_AOF", "everysec"),
        ("AOF", "URING_AOF", "no"),
        ("RDB", "AOF", "always"),
    ]
    plot_types = ["cpu", "mem", "syscall", "syscalltime", "rps"]
    labels = {
        "RDB": "RDB",
        "AOF": "AOF",
        "URING_AOF": "URING AOF",
        "URING_AOF_SQPOLL": "URING AOF SQPOLL",
    }
    colors = {
        "RDB": "green",
        "AOF": "blue",
        "URING_AOF": "red",
        "URING_AOF_SQPOLL": "purple",
    }

    file_patterns = {
        "cpu": "{fsync_type}{count}_avg_usage.csv",
        "mem": "{fsync_type}{count}_avg_usage.csv",
        "syscall": "{fsync_type}{count}_syscalls_avg.csv",
        "syscalltime": "{fsync_type}{count}_syscalls-times_avg.csv",
        "rps": "{fsync_type}{count}_avg.csv",
    }

    for count in request_counts:
        for comp in comparisons:
            dir1, dir2, fsync_type = comp
            if dir1 == "RDB":
                fsync_type2 = fsync_type + "_"
                fsync_type = ""
            elif dir2 == "RDB":
                fsync_type2 = ""
                fsync_type = fsync_type + "_"
            else:
                fsync_type2 = fsync_type + "_"
                fsync_type = fsync_type + "_"
            if dir1 not in dirnames or dir2 not in dirnames:
                continue
            base_name = f"{dir1}_vs_{dir2}_{fsync_type}_{count}"
            dir = os.path.join(graphs_dir, f"{dir1}_vs_{dir2}")
            os.makedirs(dir, exist_ok=True)
            for plot_type in plot_types:
                csv1 = file_patterns[plot_type].format(
                    fsync_type=fsync_type, count=count
                )
                csv2 = file_patterns[plot_type].format(
                    fsync_type=fsync_type2, count=count
                )
                csv1 = os.path.join("benchmarks", dir1, "csvs", csv1)
                csv2 = os.path.join("benchmarks", dir2, "csvs", csv2)
                print(f"csv1: {csv1}")
                print(f"Plotting {plot_type} for {base_name}")
                if os.path.exists(csv1) and os.path.exists(csv2):
                    subprocess.run(
                        [
                            "python3",
                            "plot.py",
                            "--gt",
                            plot_type,
                            "--csv1",
                            csv1,
                            "--csv2",
                            csv2,
                            "--dir",
                            graphs_dir,
                            "--l1",
                            labels[dir1],
                            "--l2",
                            labels[dir2],
                            "--c1",
                            colors[dir1],
                            "--c2",
                            colors[dir2],
                            "--name",
                            f"{dir1}_vs_{dir2}/{plot_type}_{base_name}",
                        ]
                    )


def find_benchmark_scripts(path, passed=False):
    benchmark_scripts = {}
    if os.path.isfile(path) and path.endswith(".py"):
        dirname = os.path.basename(os.path.dirname(path))
        if dirname not in benchmark_scripts:
            benchmark_scripts[dirname] = []
        benchmark_scripts[dirname].append(path)
    elif os.path.isdir(path) and not passed:
        for subdir in os.listdir(path):
            subdir_path = os.path.join(path, subdir)
            if os.path.isdir(subdir_path):
                scripts = []
                for root, _, files in os.walk(subdir_path):
                    for file in files:
                        if file.endswith(".py"):
                            scripts.append(os.path.join(root, file))
                if scripts:
                    benchmark_scripts[subdir] = scripts
    elif os.path.isdir(path) and passed:
        scripts = []
        for root, _, files in os.walk(path):
            for file in files:
                if file.endswith(".py"):
                    scripts.append(os.path.join(root, file))
        if scripts:
            dir_name = os.path.basename(path)
            benchmark_scripts[dir_name] = scripts
        return benchmark_scripts


if __name__ == "__main__":
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
        parser.add_argument(
            "--requests",
            type=str,
            default="100000",
            help="Comma-separated list of request counts",
        )
        parser.add_argument(
            "--plot",
            action="store_true",
            help="Flag to generate plots after running benchmarks",
        )
        args = parser.parse_args()
        request_counts = list(map(int, args.requests.split(",")))

        benchmark_scripts = {}
        if not args.paths:
            benchmark_scripts.update(find_benchmark_scripts("benchmarks"))
        else:
            for path in args.paths:
                path = path.rstrip("/")
                benchmark_scripts.update(find_benchmark_scripts(path, True))

        sorted_directories = sorted(benchmark_scripts.keys())

        for dirname in sorted_directories:
            print(f"{dirname}")
            for script in benchmark_scripts[dirname]:
                run_benchmark_script(script, args.iterations, request_counts)

        if args.plot:
            print("Generating plots...")
            plot_comparisons("graphs", request_counts, sorted_directories)
    finally:
        print("All benchmark tests completed successfully.")
        sys.exit(0)
