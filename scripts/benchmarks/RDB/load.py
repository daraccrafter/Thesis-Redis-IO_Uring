import sys
import os
import redis
import time
import threading

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from util import (
    run_server,
    stop_server,
    run_benchmark,
    kill_process_on_port,
    monitor_process,
    calc_avg_usages,
    average_load_csv_files,
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
    kill_process_on_port(6381)
    process = run_server("redis", config_path, redis_log_path, 6381)
    r = redis.Redis(host="localhost", port=6381)
    print("\tLoad")
    for i in range(1, iterations + 1):
        for count in request_counts:
            cpu_usages, memory_usages = [], []
            stop_event = threading.Event()
            monitor_thread = threading.Thread(
                target=monitor_process,
                args=(process.pid, stop_event, cpu_usages, memory_usages),
            )
            monitor_thread.start()
            run_benchmark(count, csvs_dir_path, 6381, i, False)
            stop_event.set()
            monitor_thread.join()
            calc_avg_usages(cpu_usages, memory_usages, csvs_dir_path, count, i)

    for count in request_counts:
        average_load_csv_files(count, csvs_dir_path, iterations)

    stop_server(process)

    exit(0)
