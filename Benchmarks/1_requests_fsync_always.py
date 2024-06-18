import subprocess
import os
from datetime import datetime
import signal
import time
import sys

benchmark = "1_requests_fsync_always"
request_counts = [1000, 10000, 100000, 1000000]

base_dir = "csvs"
redis_dir = os.path.join(base_dir, "redis")
redis_io_uring_dir = os.path.join(base_dir, "redis-io_uring")

os.makedirs(redis_dir, exist_ok=True)
os.makedirs(redis_io_uring_dir, exist_ok=True)

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

output_dir_redis = os.path.join(redis_dir, f"1-{timestamp}")
output_dir_redis_io_uring = os.path.join(redis_io_uring_dir, f"1_{timestamp}")

os.makedirs(output_dir_redis, exist_ok=True)
os.makedirs(output_dir_redis_io_uring, exist_ok=True)

redis_server_command = ["./src/redis-server", "../Configs/redis/1_redis.conf"]
redis_io_uring_server_command = ["./src/redis-server", "../Configs/redis-io_uring/1_redis.conf"]

def run_benchmark(request_count, output_dir, port):
    csv_filename = os.path.join(output_dir, f"{request_count}_numrequests.csv")
    command = ["redis-benchmark","-p", str(port), "-t", "set", "-n", str(request_count), "--csv"]
    
    with open(csv_filename, "w") as csvfile:
        subprocess.run(command, stdout=csvfile, check=True)


def start_redis_server(command, cwd):
    return subprocess.Popen(command, cwd=cwd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def stop_redis_server(process):
    process.send_signal(signal.SIGTERM)
    process.wait()

def signal_handler(sig, frame):
    print('Interrupt received, shutting down servers...')
    stop_redis_server(redis_server_process)
    stop_redis_server(redis_io_uring_server_process)
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

redis_server_process = start_redis_server(redis_server_command, cwd="redis")
redis_io_uring_server_process = start_redis_server(redis_io_uring_server_command, cwd="redis-io_uring")
time.sleep(5)

try:
    for count in request_counts:
        print(f"Running benchmark with {count} requests on Redis...")
        run_benchmark(count, output_dir_redis, 6380)
finally:
    stop_redis_server(redis_server_process)

try:
    for count in request_counts:
        print(f"Running benchmark with {count} requests on Redis io_uring...")
        run_benchmark(count, output_dir_redis_io_uring, 6379)
finally:
    stop_redis_server(redis_io_uring_server_process)

print(f"{benchmark} data has been saved in {output_dir_redis} and {output_dir_redis_io_uring}")
