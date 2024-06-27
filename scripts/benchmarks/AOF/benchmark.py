import sys
import os
import redis
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from util import (
    run_server,
    stop_server,
    run_benchmark,
    average_rps_csv_files,
    kill_process_on_port,
)

appendfsync_configs = ["always", "everysec", "no"]
currdir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(currdir, "redis.conf")
log_dir_path = os.path.join(currdir, "logs")
redis_log_path = os.path.join(log_dir_path, "redis.log")
csvs_dir_path = os.path.join(currdir, "csvs")
os.makedirs(csvs_dir_path, exist_ok=True)
os.makedirs(log_dir_path, exist_ok=True)
tempdir = os.path.join(currdir, "temp")
os.makedirs(tempdir, exist_ok=True)

if len(sys.argv) != 3:
    print("Arg error")
    exit(1)

iterations = int(sys.argv[1])
request_counts = list(map(int, sys.argv[2].split(",")))

if __name__ == "__main__":
    kill_process_on_port(6380)
    process = run_server("redis", config_path, redis_log_path, 6380)
    r = redis.Redis(host="localhost", port=6380)
    print("\tBenchmark")
    for i in range(1, iterations + 1):
        for fsync in appendfsync_configs:
            r.config_set("appendfsync", fsync)
            for count in request_counts:
                run_benchmark(count, csvs_dir_path, 6380, i, fsync)

    for count in request_counts:
        for fsync in appendfsync_configs:
            filename_pattern = f"{fsync}_{count}_run{{iteration}}.csv"
            average_rps_csv_files(
                csvs_dir_path, iterations, filename_pattern, f"{fsync}_{count}_avg.csv"
            )

    stop_server(process)

    exit(0)
