import sys
import os
import signal
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from benchmark_util import (
    create_directories,
    run_benchmark,
    average_syscall_times_csv_files,
    average_syscalls_files,
    plot_syscall_times_comparison,
    plot_syscalls_comparison,
    run_strace,
    load_config,
)

currdir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(currdir, "config.yaml")
config = load_config(config_path)

if len(sys.argv) != 6:
    print(
        f"Usage: {config['benchmark']}.py <timestamp> <iterations> <pid_redis_aof> <pid_redis_rdb> <request_counts>"
    )
    exit(1)

timestamp = sys.argv[1]
iterations = int(sys.argv[2])
pid_redis_aof = int(sys.argv[3])
pid_redis_rdb = int(sys.argv[4])
request_counts = list(map(int, sys.argv[5].split(",")))

(
    output_dir_redis_aof,
    output_dir_redis_rdb,
    graphs_dir,
    logs_dir_redis_aof,
    logs_dir_redis_rdb,
) = create_directories(
    str(currdir), timestamp, config["server1_data_dir"], config["server2_data_dir"]
)

if __name__ == "__main__":

    for i in range(1, iterations + 1):
        print(f"\tIteration {i}:")
        for count in request_counts:
            print(
                f"\t\tRunning benchmark with {count} requests on Redis AOF..."
            )
            strace_process = run_strace(
                pid_redis_aof,
                count,
                output_dir_redis_aof,
                logs_dir_redis_aof,
                i,
            )
            time.sleep(0.5)
            run_benchmark(count, output_dir_redis_aof, 6379, i, "", False)
            time.sleep(0.5)
            strace_process.send_signal(signal.SIGINT)
            strace_process.wait()

        for count in request_counts:
            print(f"\t\tRunning benchmark with {count} requests on Redis RDB...")
            strace_process = run_strace(
                pid_redis_rdb, count, output_dir_redis_rdb, logs_dir_redis_rdb, i
            )
            time.sleep(0.5)
            run_benchmark(count, output_dir_redis_rdb, 6380, i, "", False)
            time.sleep(0.5)
            strace_process.send_signal(signal.SIGINT)
            strace_process.wait()

    for count in request_counts:
        filename_pattern_syscalls = f"_syscalls_{count}_run{{iteration}}.csv"
        filename_pattern_syscall_times = f"_syscalls_times_{count}_run{{iteration}}.csv"
        avg_syscalls_redis_aof = average_syscalls_files(
            output_dir_redis_aof,
            iterations,
            filename_pattern_syscalls,
            f"syscalls_{count}_avg.csv",
        )
        avg_syscalls_redis_rdb = average_syscalls_files(
            output_dir_redis_rdb,
            iterations,
            filename_pattern_syscalls,
            f"syscalls_{count}_avg.csv",
        )
        avg_syscalls_times_redis_aof = average_syscall_times_csv_files(
            output_dir_redis_aof,
            iterations,
            filename_pattern_syscall_times,
            f"syscalls_times_{count}_avg.csv",
        )
        avg_syscalls_times_redis_rdb = average_syscall_times_csv_files(
            output_dir_redis_rdb,
            iterations,
            filename_pattern_syscall_times,
            f"syscalls_times_{count}_avg.csv",
        )
        plot_syscalls_comparison(
            avg_syscalls_redis_rdb,
            avg_syscalls_redis_aof,
            count,
            graphs_dir,
            label_1="Redis RDB",
            label_2="Redis AOF (appendfsync=always)",
            bar_1_color="green",
            bar_2_color="blue",
        )
        plot_syscall_times_comparison(
            avg_syscalls_times_redis_rdb,
            avg_syscalls_times_redis_aof,
            count,
            graphs_dir,
            label_1="Redis RDB",
            label_2="Redis AOF (appendfsync=always)",
            bar_1_color="green",
            bar_2_color="blue",
        )

    exit(0)
