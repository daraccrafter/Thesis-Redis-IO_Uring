import sys
import os
import threading

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from benchmark_util import (
    create_directories,
    run_benchmark,
    monitor_process,
    average_load_csv_files,
    load_config,
    calc_avg_usages,
    plot_cpu_comparison,
    plot_memory_comparison,
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

output_dir_redis_aof, output_dir_redis_rdb, graphs_dir, _, _ = create_directories(
    str(currdir), timestamp, config["server1_data_dir"], config["server2_data_dir"]
)

if __name__ == "__main__":
    for i in range(1, iterations + 1):
        print(f"\tIteration {i}:")
        for count in request_counts:
            print(f"\t\tRunning benchmark with {count} requests on Redis AOF...")
            cpu_usages, memory_usages = [], []
            stop_event = threading.Event()
            monitor_thread = threading.Thread(
                target=monitor_process,
                args=(pid_redis_aof, stop_event, cpu_usages, memory_usages),
            )
            monitor_thread.start()
            run_benchmark(count, output_dir_redis_aof, 6379, i, "", False)
            stop_event.set()
            monitor_thread.join()
            calc_avg_usages(cpu_usages, memory_usages, output_dir_redis_aof, count, i)
        for count in request_counts:
            print(f"\t\tRunning benchmark with {count} requests on Redis RDB...")
            cpu_usages_1, memory_usages_1 = [], []
            stop_event = threading.Event()
            monitor_thread = threading.Thread(
                target=monitor_process,
                args=(pid_redis_rdb, stop_event, cpu_usages_1, memory_usages_1),
            )
            monitor_thread.start()
            run_benchmark(count, output_dir_redis_rdb, 6380, i, "", False)
            stop_event.set()
            monitor_thread.join()
            calc_avg_usages(
                cpu_usages_1, memory_usages_1, output_dir_redis_rdb, count, i
            )

    for count in request_counts:
        filename_pattern = f"{count}_run{{iteration}}.csv"
        avg_redis_aof = average_load_csv_files(count, output_dir_redis_aof, iterations)
        avg_redis_rdb = average_load_csv_files(count, output_dir_redis_rdb, iterations)
        plot_memory_comparison(
            avg_redis_rdb,
            avg_redis_aof,
            count,
            graphs_dir,
            label_1="RDB",
            label_2="AOF (appendfsync=always)",
            bar_1_color="green",
            bar_2_color="blue",
        )
        plot_cpu_comparison(
            avg_redis_rdb,
            avg_redis_aof,
            count,
            graphs_dir,
            label_1="RDB",
            label_2="AOF (appendfsync=always)",
            bar_1_color="green",
            bar_2_color="blue",
        )

    exit(0)
