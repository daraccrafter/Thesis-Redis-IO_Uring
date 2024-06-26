import sys
import os
import redis
import subprocess
import concurrent.futures

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from benchmark_util import (
    run_server,
    stop_server,
    kill_process_on_port,
    remove_appendonlydir,
    check_aof_file,
    make_requests,
    verify_keys,
)

appendfsync_configs = ["always", "everysec", "no"]
currdir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(currdir, "data-redis.conf")
log_dir_path = os.path.join(currdir, "logs")
redis_log_path = os.path.join(log_dir_path, "redis.log")
csvs_dir_path = os.path.join(currdir, "csvs")
tempdir = os.path.join(currdir, "temp-integrity")
os.makedirs(csvs_dir_path, exist_ok=True)
os.makedirs(log_dir_path, exist_ok=True)
os.makedirs(tempdir, exist_ok=True)

if len(sys.argv) != 3:
    print("Arg error")
    exit(1)

iterations = int(sys.argv[1])
request_counts = list(map(int, sys.argv[2].split(",")))


if __name__ == "__main__":
    remove_appendonlydir(tempdir)
    kill_process_on_port(6383)
    process = run_server("redis-io_uring", config_path, redis_log_path, 6383)
    r = redis.Redis(host="localhost", port=6383)
    print("\tData check")
    max_workers = 300
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = []
        futures.append(executor.submit(make_requests, r, max(request_counts)))
        concurrent.futures.wait(futures)

    stop_server(process)
    check_aof_file(tempdir, log_dir_path)
    process = run_server("redis-io_uring", config_path, redis_log_path, 6383)
    r = redis.Redis(host="localhost", port=6383)
    verify_keys(r, max(request_counts), csvs_dir_path, log_dir_path)
    stop_server(process)

    exit(0)
