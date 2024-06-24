import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from benchmark_util import (
    create_directories,
    run_benchmark,
    average_rps_csv_files,
    plot_rps_comparison,
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
pid_redis = int(sys.argv[3])
pid_redis_io_uring = int(sys.argv[4])
request_counts = list(map(int, sys.argv[5].split(",")))

output_dir_redis, output_dir_redis_io_uring, graphs_dir, _, _ = create_directories(
    str(currdir), timestamp
)


if __name__ == "__main__":
    for i in range(1, iterations + 1):
        print(f"\tIteration {i}:")
        for count in request_counts:
            print(f"\t\tRunning benchmark with {count} requests on Redis IO_Uring...")
            run_benchmark(count, output_dir_redis_io_uring, 6379, i)
        for count in request_counts:
            print(f"\t\tRunning benchmark with {count} requests on Redis RDB...")
            run_benchmark(count, output_dir_redis, 6380, i)

    for count in request_counts:
        filename_pattern = f"{count}_run{{iteration}}.csv"
        avg_redis = average_rps_csv_files(
            output_dir_redis, iterations, filename_pattern, f"{count}_avg.csv"
        )
        avg_redis_io_uring = average_rps_csv_files(
            output_dir_redis_io_uring, iterations, filename_pattern, f"{count}_avg.csv"
        )
        plot_rps_comparison(
            avg_redis,
            avg_redis_io_uring,
            count,
            graphs_dir,
            label_1="RDB",
            label_2="AOF IO_Uring (appendfsync=always)",
            bar_1_color="green",
            bar_2_color="red",
        )

    exit(0)
