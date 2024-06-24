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
        f"Usage: {config['benchmark']}.py <timestamp> <iterations> <pid_redis> <pid_redis_io_uring> <request_counts>"
    )
    exit(1)

timestamp = sys.argv[1]
iterations = int(sys.argv[2])
pid_redis_io_uring_sqpoll = int(sys.argv[3])
pid_redis_io_uring = int(sys.argv[4])
request_counts = list(map(int, sys.argv[5].split(",")))

(
    output_dir_redis_io_uring_sqpoll,
    output_dir_redis_io_uring,
    graphs_dir,
    logs_dir_redis_sqpoll,
    logs_dir_redis_io_uring,
) = create_directories(
    str(currdir), timestamp, config["server1_data_dir"], config["server2_data_dir"]
)

if __name__ == "__main__":

    for i in range(1, iterations + 1):
        print(f"\tIteration {i}:")
        for count in request_counts:
            print(
                f"\t\tRunning benchmark with {count} requests on Redis AOF IO_Uring SQPOLL..."
            )
            strace_process = run_strace(
                pid_redis_io_uring_sqpoll,
                count,
                output_dir_redis_io_uring_sqpoll,
                logs_dir_redis_sqpoll,
                i,
            )
            time.sleep(0.5)
            run_benchmark(count, output_dir_redis_io_uring_sqpoll, 6379, i, "", False)
            time.sleep(0.5)
            strace_process.send_signal(signal.SIGINT)
            strace_process.wait()

        for count in request_counts:
            print(
                f"\t\tRunning benchmark with {count} requests on Redis IO_URING AOF..."
            )
            strace_process = run_strace(
                pid_redis_io_uring,
                count,
                output_dir_redis_io_uring,
                logs_dir_redis_io_uring,
                i,
            )
            time.sleep(0.5)
            run_benchmark(count, output_dir_redis_io_uring, 6380, i, "", False)
            time.sleep(0.5)
            strace_process.send_signal(signal.SIGINT)
            strace_process.wait()

    for count in request_counts:
        filename_pattern_syscalls = f"_syscalls_{count}_run{{iteration}}.csv"
        filename_pattern_syscall_times = f"_syscalls_times_{count}_run{{iteration}}.csv"
        avg_syscalls_redis_io_uring_sqpoll = average_syscalls_files(
            output_dir_redis_io_uring_sqpoll,
            iterations,
            filename_pattern_syscalls,
            f"syscalls_{count}_avg.csv",
        )
        avg_syscalls_redis_io_uring = average_syscalls_files(
            output_dir_redis_io_uring,
            iterations,
            filename_pattern_syscalls,
            f"syscalls_{count}_avg.csv",
        )
        avg_syscalls_times_redis_io_uring_sqpoll = average_syscall_times_csv_files(
            output_dir_redis_io_uring_sqpoll,
            iterations,
            filename_pattern_syscall_times,
            f"syscalls_times_{count}_avg.csv",
        )
        avg_syscalls_times_redis_io_uring = average_syscall_times_csv_files(
            output_dir_redis_io_uring,
            iterations,
            filename_pattern_syscall_times,
            f"syscalls_times_{count}_avg.csv",
        )
        plot_syscalls_comparison(
            avg_syscalls_redis_io_uring_sqpoll,
            avg_syscalls_redis_io_uring,
            count,
            graphs_dir,
            label_1="Redis AOF IO_Uring SQPOLL (appendfsync=always)",
            label_2="Redis AOF IO_Uring (appendfsync=always)",
            bar_1_color="purple",
            bar_2_color="red",
        )
        plot_syscall_times_comparison(
            avg_syscalls_times_redis_io_uring_sqpoll,
            avg_syscalls_times_redis_io_uring,
            count,
            graphs_dir,
            label_1="Redis AOF IO_Uring SQPOLL (appendfsync=always)",
            label_2="Redis AOF IO_Uring (appendfsync=always)",
            bar_1_color="purple",
            bar_2_color="red",
        )

    exit(0)
