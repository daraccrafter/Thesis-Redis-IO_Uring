import sys
import os
import redis
import concurrent.futures
import time
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from benchmarks.util import (
    run_server,
    stop_server,
    kill_process_on_port,
    remove_appendonlydir,
    check_aof_file,
    verify_keys,
)

currdir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(currdir,"data-redis.conf")
log_dir_path = os.path.join(currdir, "persistance-data", "logs")
redis_log_path = os.path.join("persistance-data", log_dir_path, "integrity_redis.log")
csvs_dir_path = os.path.join(currdir, "persistance-data", "csvs")
tempdir = os.path.join(currdir, "persistance-data", "temp-integrity")
os.makedirs(csvs_dir_path, exist_ok=True)
os.makedirs(log_dir_path, exist_ok=True)
os.makedirs(tempdir, exist_ok=True)

if len(sys.argv) != 2:
    print("Arg error")
    exit(1)

request_count = int(sys.argv[1])

def make_requests_test1(client, count):
    for i in range(1, count + 1):
        client.set(f"key_{i}", i)


def increment_key(client, key, count):
    for _ in range(count):
        client.incr(key)


if __name__ == "__main__":
    kill_process_on_port(6383)
    print(
        "Testing data integrity 1000 requests, 1000 incrementing keys and 1000 incrementing values."
    )
    remove_appendonlydir(tempdir)
    time.sleep(1)
    process = run_server("redis-io_uring", config_path, redis_log_path, 6383)
    r = redis.Redis(host="localhost", port=6383)
    max_workers = 100
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = []
        futures.append(executor.submit(make_requests_test1, r, request_count))
        concurrent.futures.wait(futures)

    stop_server(process)
    check_aof_file(tempdir, log_dir_path)
    process = run_server("redis-io_uring", config_path, redis_log_path, 6383)
    r = redis.Redis(host="localhost", port=6383)
    incorrect, correct = verify_keys(r, request_count, csvs_dir_path, log_dir_path)
    print(f"\tCorrect keys {len(correct)} ")
    print(f"\tIncorrect keys {len(incorrect)} ")
    print("Testing data integrity 1000 requests incr a value.")
    r.set("incr_key_1", 0)
    max_workers = 100
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = []
        futures.append(executor.submit(increment_key, r, "incr_key_1", request_count))
        concurrent.futures.wait(futures)
    stop_server(process)
    check_aof_file(tempdir, log_dir_path)
    process = run_server("redis-io_uring", config_path, redis_log_path, 6383)
    r = redis.Redis(host="localhost", port=6383)
    result = f"{request_count}"
    if r.get("incr_key_1").decode("utf-8") == result:
        val = "Correct"
    else:
        val = "Incorrect"
    print(f"\t{val}")
    exit(0)
