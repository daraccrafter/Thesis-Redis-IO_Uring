import subprocess
import os
import sys
import pandas as pd
import matplotlib.pyplot as plt

benchmark = "0_requests_aof_rdb"
request_counts = [1000000]

base_csv_dir = "csvs"
base_graphs_dir = "graphs"

if len(sys.argv) != 5:
    print(
        f"Usage: {benchmark}.py <timestamp> <iterations> <pid_redis> <pid_redis_rdb>"
    )
    exit(1)

timestamp = sys.argv[1]
iterations = int(sys.argv[2])
pid_redis = int(sys.argv[3])
pid_redis_rdb = int(sys.argv[4])

output_dir_redis = os.path.join(base_csv_dir, "redis", "0", timestamp)
graphs_dir = os.path.join(base_graphs_dir, "0", timestamp)
os.makedirs(output_dir_redis, exist_ok=True)
os.makedirs(graphs_dir, exist_ok=True)


def run_benchmark(request_count, output_dir, port, iteration, persistance):
    csv_filename = os.path.join(
        output_dir, f"{persistance}_{request_count}_run{iteration}.csv"
    )
    command = [
        "./redis-benchmark",
        "-p",
        str(port),
        "-t",
        "set,lpush",
        "-n",
        str(request_count),
        "--csv",
    ]

    with open(csv_filename, "w") as csvfile:
        subprocess.run(command, stdout=csvfile, check=True)


def average_csv_files(request_count, output_dir, iterations, persistance):
    files = [
        os.path.join(output_dir, f"{persistance}_{request_count}_run{i}.csv")
        for i in range(1, iterations + 1)
    ]
    df_list = [pd.read_csv(file) for file in files]

    df_combined = pd.concat(df_list)
    df_avg = df_combined.groupby("test").mean().reset_index()

    avg_csv_filename = os.path.join(
        output_dir, f"avg_{persistance}_{request_count}.csv"
    )
    df_avg.to_csv(avg_csv_filename, index=False)

    return df_avg


def plot_rps_comparison(df_avg_redis, df_avg_redis_rdb, request_count):
    labels = df_avg_redis["test"]
    redis_rps = df_avg_redis["rps"]
    redis_io_uring_rps = df_avg_redis_rdb["rps"]

    x = range(len(labels))
    bar_width = 0.35

    plt.figure(figsize=(10, 6))

    bar_positions_redis = [p - bar_width / 2 for p in x]
    bar_positions_io_uring = [p + bar_width / 2 for p in x]

    plt.bar(
        bar_positions_redis,
        redis_rps,
        width=bar_width,
        label="Redis RDB",
        color="green",
    )
    plt.bar(
        bar_positions_io_uring,
        redis_io_uring_rps,
        width=bar_width,
        label="Redis AOF (appendfsync = always)",
        color="blue",
    )

    plt.xlabel("Operation", fontsize=12)
    plt.ylabel("Requests per second (RPS)", fontsize=12)

    combined_positions = [
        (bar_positions_redis[i] + bar_positions_io_uring[i]) / 2
        for i in range(len(labels))
    ]
    plt.xticks(ticks=combined_positions, labels=labels, rotation=0)

    plt.legend(loc="upper center", bbox_to_anchor=(0.5, 1.15), ncol=2)
    plt.grid(True, axis="y", linestyle="--", alpha=0.7)
    plt.tight_layout()

    plot_filename = os.path.join(graphs_dir, f"{request_count}_rps.png")
    plt.savefig(plot_filename, bbox_inches="tight")
    plt.close()


if __name__ == "__main__":
    for i in range(1, iterations + 1):
        print(f"\tIteration {i}:")
        for count in request_counts:
            print(f"\t\tRunning benchmark with {count} requests on Redis RDB...")
            run_benchmark(count, output_dir_redis, 6379, i, "rdb")
        for count in request_counts:
            print(f"\t\tRunning benchmark with {count} requests on Redis...")
            run_benchmark(count, output_dir_redis, 6380, i, "aof")

    for count in request_counts:
        avg_redis_rdb = average_csv_files(count, output_dir_redis, iterations,"rdb")
        avg_redis = average_csv_files(count, output_dir_redis, iterations,"aof")

        plot_rps_comparison(avg_redis_rdb, avg_redis, count)

    exit(0)
